"""
Seed realistic demo data so the calendar, charts and review queue have
something real to show. Marked demo via a dedicated account name so it can
be wiped with --wipe. No lorem, no fictional tickers — real FX pairs only.
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.accounts.models import TradingAccount
from app.journal.models import TradeReview
from app.trades.models import Strategy, Tag, Trade, pip_size

DEMO_ACCOUNT = "Demo (seeded)"

PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "AUDUSD", "XAUUSD", "EURGBP"]
STRATEGIES = [
    ("London Breakout", "Trade the range break at the London open."),
    ("Trend Pullback", "Enter on a pullback to the 20 EMA in a clear trend."),
    ("Support/Resistance", "Fade reactions at marked key levels."),
]
TAGS = ["A+ setup", "news", "scalp", "swing", "revenge-trade"]


class Command(BaseCommand):
    help = "Seed realistic demo trades, strategies and some reviews."

    def add_arguments(self, parser):
        parser.add_argument("--trades", type=int, default=60)
        parser.add_argument("--wipe", action="store_true", help="Remove seeded demo data")

    def handle(self, *args, **opts):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="admin", defaults={"is_staff": True, "is_superuser": True}
        )
        if created:
            user.set_password("admin123")
            user.save()
            self.stdout.write(self.style.WARNING("Created user 'admin' / password 'admin123'"))

        account, _ = TradingAccount.objects.get_or_create(
            owner=user, name=DEMO_ACCOUNT,
            defaults={"broker": "Demo Broker", "currency": "USD",
                      "balance": Decimal("10000.00"), "is_default": True},
        )

        if opts["wipe"]:
            n = Trade.objects.filter(account=account).count()
            Trade.objects.filter(account=account).delete()
            self.stdout.write(self.style.SUCCESS(f"Wiped {n} demo trades."))
            return

        strategies = [
            Strategy.objects.get_or_create(name=n, defaults={"description": d})[0]
            for n, d in STRATEGIES
        ]
        tags = [Tag.objects.get_or_create(name=t)[0] for t in TAGS]

        rng = random.Random(42)  # reproducible
        now = timezone.now()
        created = 0
        for i in range(opts["trades"]):
            symbol = rng.choice(PAIRS)
            direction = rng.choice(["buy", "sell"])
            pip = pip_size(symbol)
            entry = self._entry_price(symbol, rng)
            # Win ~55% of the time; size the move in pips.
            win = rng.random() < 0.55
            move_pips = rng.randint(8, 60) * (1 if win else -1)
            signed = move_pips if direction == "buy" else move_pips
            exit_price = entry + Decimal(str(move_pips * pip)) * (1 if direction == "buy" else -1)

            volume = Decimal(rng.choice(["0.10", "0.20", "0.50", "1.00"]))
            # Rough USD P/L: pips * pip-value-per-lot * lots.
            pip_value = Decimal("10") if symbol != "XAUUSD" else Decimal("1")
            profit = (Decimal(move_pips) * pip_value * volume).quantize(Decimal("0.01"))

            days_ago = rng.randint(0, 42)
            entry_time = now - timedelta(days=days_ago, hours=rng.randint(0, 10))
            exit_time = entry_time + timedelta(hours=rng.randint(1, 20))

            trade = Trade.objects.create(
                account=account, symbol=symbol, direction=direction, volume=volume,
                entry_price=entry, exit_price=exit_price.quantize(Decimal("0.00001")),
                sl=(entry - Decimal(str(30 * pip))).quantize(Decimal("0.00001")),
                tp=(entry + Decimal(str(60 * pip))).quantize(Decimal("0.00001")),
                entry_time=entry_time, exit_time=exit_time,
                profit=profit, commission=Decimal("-0.70") * volume, swap=Decimal("0"),
                strategy=rng.choice(strategies), status=Trade.Status.CLOSED,
                source=Trade.Source.IMPORT,
            )
            trade.tags.add(rng.choice(tags))

            # Complete reviews for older trades; leave recent ones pending.
            if days_ago > 3 and rng.random() < 0.6:
                TradeReview.objects.create(
                    trade=trade, followed_plan=win,
                    emotion=rng.choice([e.value for e in TradeReview.Emotion]),
                    what_went_well="Entry aligned with the setup." if win else "",
                    what_went_wrong="" if win else "Chased the entry past the level.",
                    lesson="Wait for confirmation.", rating=rng.randint(2, 5),
                )
                trade.review_completed = True
                trade.save(update_fields=["review_completed"])
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created} demo trades across {len(PAIRS)} pairs. "
            f"Some reviews left pending on purpose."
        ))

    @staticmethod
    def _entry_price(symbol, rng):
        base = {
            "EURUSD": "1.0850", "GBPUSD": "1.2700", "USDJPY": "150.50",
            "GBPJPY": "191.20", "AUDUSD": "0.6600", "XAUUSD": "2650.00",
            "EURGBP": "0.8350",
        }[symbol]
        jitter = Decimal(str(rng.uniform(-0.5, 0.5)))
        return (Decimal(base) + jitter).quantize(Decimal("0.00001"))
