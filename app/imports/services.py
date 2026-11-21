"""Turn parsed MT5 rows into Trade records. Idempotent via mt5_ticket."""

from app.trades.models import Trade

from .models import ImportBatch


def import_rows(account, rows, kind="csv", source_name=""):
    created = skipped = 0
    for row in rows:
        ticket = row.get("mt5_ticket")
        if ticket and Trade.objects.filter(mt5_ticket=ticket).exists():
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
