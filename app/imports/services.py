"""Turn MT5 payloads into Trade records."""

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from collections import Counter
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from app.trades.models import Trade
from core.lib.mt5.myfxbook import MyfxbookClient, MyfxbookError

from .models import ImportBatch


def link_plan_to_trade(plan, trade):
    """Merge a plan (floating idea) into the real booked trade, then archive the
    plan. The broker book stays the source of truth for numbers; the plan only
    contributes the captured moment: journal, screenshots, strategy, tags, thesis.
    """
    from app.trades.models import Trade

    # Move the captured journal and screenshots onto the real trade.
    plan.journal_blocks.update(trade=trade)
    plan.images.update(trade=trade)

    # Carry over setup metadata where the real trade has none.
    if plan.strategy_id and not trade.strategy_id:
        trade.strategy_id = plan.strategy_id
    tag_ids = list(plan.tags.values_list("id", flat=True))
    if tag_ids:
        trade.tags.add(*tag_ids)
    if plan.notes:
        trade.notes = f"{trade.notes}\n\n{plan.notes}".strip() if trade.notes else plan.notes

    trade.confirmed = True
    trade.save()

    plan.plan_status = Trade.PlanStatus.REALIZED
    plan.realized_trade = trade
    plan.save(update_fields=["plan_status", "realized_trade"])
    return trade


def import_rows(account, rows, kind="csv", source_name=""):
    created = skipped = 0
    for row in rows:
        ticket = row.get("mt5_ticket")
        if ticket and Trade.objects.filter(account=account, mt5_ticket=ticket).exists():
            skipped += 1
            continue
        status = Trade.Status.CLOSED if row.get("exit_time") else Trade.Status.OPEN
        Trade.objects.create(
            account=account,
            mt5_ticket=ticket,
            symbol=row["symbol"],
            direction=row["direction"],
            volume=row["volume"],
            entry_price=row["entry_price"],
            exit_price=row.get("exit_price"),
            sl=row.get("sl"),
            tp=row.get("tp"),
            entry_time=row["entry_time"],
            exit_time=row.get("exit_time"),
            profit=row.get("profit", 0),
            commission=row.get("commission", 0),
            swap=row.get("swap", 0),
            status=status,
            source=Trade.Source.IMPORT,
            confirmed=False,
        )
        created += 1

    batch = ImportBatch.objects.create(
        account=account,
        kind=kind,
        source_name=source_name,
        rows_parsed=len(rows),
        rows_created=created,
        rows_skipped=skipped,
    )
    return batch


def _decimal(value, default="0"):
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _myfxbook_datetime(value):
    parsed = datetime.strptime(value, "%m/%d/%Y %H:%M")
    return parsed.replace(tzinfo=ZoneInfo(settings.MYFXBOOK_BROKER_TIMEZONE))


def _myfxbook_direction(action):
    return Trade.Direction.BUY if "buy" in str(action).lower() else Trade.Direction.SELL


def _myfxbook_volume(item):
    sizing = item.get("sizing") or {}
    return _decimal(sizing.get("value") if isinstance(sizing, dict) else sizing, "0.01")


def _signature(item, include_close=False):
    fields = {
        "openDate": item.get("openDate") or item.get("openTime"),
        "symbol": item.get("symbol"),
        "action": item.get("action"),
        "volume": str(_myfxbook_volume(item)),
        "openPrice": item.get("openPrice"),
    }
    if include_close:
        fields.update({
            "closeDate": item.get("closeDate") or item.get("closeTime"),
            "closePrice": item.get("closePrice"),
            "profit": item.get("profit"),
            "commission": item.get("commission"),
            "interest": item.get("interest"),
        })
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()[:32]


def _renew_myfxbook_session(connection):
    """Renew an expired IP-bound session using server-only credentials."""
    email = os.environ.get("MYFXBOOK_EMAIL")
    password = os.environ.get("MYFXBOOK_PASSWORD")
    if not email or not password:
        raise MyfxbookError(
            "The Myfxbook session expired. Reconnect it in the journal, or configure "
            "MYFXBOOK_EMAIL and MYFXBOOK_PASSWORD on the server for automatic renewal."
        )

    client = MyfxbookClient(email=email, password=password)
    session = client.authenticate()
    accounts = client.get_accounts()
    selected = next(
        (item for item in accounts if str(item.get("accountId")) == str(connection.account.login)),
        None,
    )
    if selected is None:
        client.logout()
        raise MyfxbookError("The configured MT5 account was not returned by this Myfxbook login.")

    connection.myfxbook_session = session
    connection.myfxbook_account_id = str(selected["id"])
    connection.session_expires_at = timezone.now() + timedelta(days=29)
    connection.state = "connected"
    connection.last_error = ""
    connection.save(update_fields=[
        "myfxbook_session", "myfxbook_account_id", "session_expires_at", "state", "last_error"
    ])
    return client


def _myfxbook_payload(connection):
    """Fetch all documented account-state collections, renewing once if needed."""
    expired = not connection.session_expires_at or connection.session_expires_at <= timezone.now()
    client = _renew_myfxbook_session(connection) if expired else MyfxbookClient()
    client.session = connection.myfxbook_session
    try:
        return (
            client.get_open_trades(connection.myfxbook_account_id),
            client.get_open_orders(connection.myfxbook_account_id),
            client.get_history(connection.myfxbook_account_id),
        )
    except MyfxbookError as exc:
        if "invalid session" not in str(exc).lower():
            raise
        client = _renew_myfxbook_session(connection)
        return (
            client.get_open_trades(connection.myfxbook_account_id),
            client.get_open_orders(connection.myfxbook_account_id),
            client.get_history(connection.myfxbook_account_id),
        )


def sync_myfxbook_connection(connection):
    """Persist Myfxbook's open trades and latest-50 history without losing older rows."""
    open_items, open_orders, history_items = _myfxbook_payload(connection)
    created = updated = 0
    occurrences = Counter()

    for item in open_items:
        base = _signature(item)
        occurrences[base] += 1
        external_key = f"open:{base}:{occurrences[base]}"
        defaults = {
            "symbol": item["symbol"].upper(),
            "direction": _myfxbook_direction(item.get("action")),
            "volume": _myfxbook_volume(item),
            "entry_price": _decimal(item.get("openPrice")),
            "sl": _decimal(item["sl"]) if item.get("sl") else None,
            "tp": _decimal(item["tp"]) if item.get("tp") else None,
            "entry_time": _myfxbook_datetime(item.get("openTime") or item.get("openDate")),
            "profit": _decimal(item.get("profit")),
            "swap": _decimal(item.get("swap")),
            "status": Trade.Status.OPEN,
            "source": Trade.Source.IMPORT,
        }
        obj, was_created = Trade.objects.update_or_create(
            account=connection.account,
            external_source="myfxbook",
            external_key=external_key,
            defaults=defaults,
        )
        if was_created and obj.confirmed:
            obj.confirmed = False
            obj.save(update_fields=["confirmed"])
        created += int(was_created)
        updated += int(not was_created)

    occurrences.clear()
    for item in history_items:
        full = _signature(item, include_close=True)
        occurrences[full] += 1
        external_key = f"history:{full}:{occurrences[full]}"
        base = _signature(item)
        trade = Trade.objects.filter(
            account=connection.account,
            external_source="myfxbook",
            external_key__startswith=f"open:{base}:",
        ).first()
        defaults = {
            "symbol": item["symbol"].upper(),
            "direction": _myfxbook_direction(item.get("action")),
            "volume": _myfxbook_volume(item),
            "entry_price": _decimal(item.get("openPrice")),
            "exit_price": _decimal(item.get("closePrice")),
            "sl": _decimal(item["sl"]) if item.get("sl") else None,
            "tp": _decimal(item["tp"]) if item.get("tp") else None,
            "entry_time": _myfxbook_datetime(item.get("openTime") or item.get("openDate")),
            "exit_time": _myfxbook_datetime(item.get("closeTime") or item.get("closeDate")),
            "profit": _decimal(item.get("profit")),
            "commission": _decimal(item.get("commission")),
            "swap": _decimal(item.get("interest")),
            "status": Trade.Status.CLOSED,
            "source": Trade.Source.IMPORT,
            "external_key": external_key,
        }
        if trade:
            for field, value in defaults.items():
                setattr(trade, field, value)
            trade.save()
            updated += 1
        else:
            obj, was_created = Trade.objects.update_or_create(
                account=connection.account,
                external_source="myfxbook",
                external_key=external_key,
                defaults=defaults,
            )
            if was_created and obj.confirmed:
                obj.confirmed = False
                obj.save(update_fields=["confirmed"])
            created += int(was_created)
            updated += int(not was_created)

    connection.last_sync_at = timezone.now()
    connection.last_history_sync_at = timezone.now()
    connection.state = "connected"
    connection.last_error = ""
    connection.save(update_fields=["last_sync_at", "last_history_sync_at", "state", "last_error"])
    return {
        "created": created,
        "updated": updated,
        "positions": len(open_items),
        "pending_orders": len(open_orders),
        "history": len(history_items),
    }
