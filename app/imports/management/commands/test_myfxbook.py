"""Verify a real Myfxbook connection without reading or writing Django models."""

import os

from django.core.management.base import BaseCommand, CommandError

from core.lib.mt5.myfxbook import MyfxbookConnector, MyfxbookError


class Command(BaseCommand):
    help = "Test Myfxbook credentials and inspect available MT5 data without changing the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--account",
            help="Myfxbook account id or MT5 account number; otherwise selects the first IC Markets account.",
        )

    def handle(self, *args, **options):
        email = os.environ.get("MYFXBOOK_EMAIL")
        password = os.environ.get("MYFXBOOK_PASSWORD")
        if not email or not password:
            raise CommandError("Set MYFXBOOK_EMAIL and MYFXBOOK_PASSWORD before running this probe.")

        connector = MyfxbookConnector(email=email, password=password)
        logged_in = False
        try:
            connector.authenticate()
            logged_in = True
            self.stdout.write(self.style.SUCCESS("Myfxbook authentication succeeded."))

            accounts = connector.get_accounts()
            self.stdout.write(f"Connected personal accounts: {len(accounts)}")
            account = self._select_account(accounts, options.get("account"))
            server = account.get("server") or {}
            server_name = server.get("name", "") if isinstance(server, dict) else str(server)
            self.stdout.write(
                f"Selected: {account.get('name') or 'Unnamed'} · MT5 #{account.get('accountId')} · "
                f"{server_name or 'server unavailable'} · {account.get('currency') or 'currency unavailable'}"
            )

            account_id = account["id"]
            history = connector.get_history(account_id)
            open_trades = connector.get_open_trades(account_id)
            open_orders = connector.get_open_orders(account_id)

            self.stdout.write(self.style.SUCCESS("Read-only data retrieval succeeded."))
            self.stdout.write(f"History returned: {len(history)} transaction(s), maximum 50")
            self.stdout.write(f"Open trades returned: {len(open_trades)}")
            self.stdout.write(f"Pending orders returned: {len(open_orders)}")
            self._print_schema("history", history)
            self._print_schema("open trade", open_trades)
            self._print_schema("pending order", open_orders)
            self.stdout.write("No database models or migrations were changed by this command.")
        except (MyfxbookError, KeyError) as exc:
            raise CommandError(str(exc)) from None
        finally:
            if logged_in:
                try:
                    connector.logout()
                    self.stdout.write("Myfxbook session logged out.")
                except MyfxbookError:
                    self.stderr.write("Warning: data retrieval finished, but Myfxbook logout failed.")

    @staticmethod
    def _select_account(accounts, requested):
        if requested:
            selected = next(
                (
                    account
                    for account in accounts
                    if str(account.get("id")) == requested or str(account.get("accountId")) == requested
                ),
                None,
            )
            if not selected:
                raise CommandError("That Myfxbook/MT5 account was not returned by get-my-accounts.")
            return selected

        selected = next(
            (
                account
                for account in accounts
                if "ic market" in " ".join(
                    (
                        str(account.get("name", "")),
                        str((account.get("server") or {}).get("name", ""))
                        if isinstance(account.get("server") or {}, dict)
                        else str(account.get("server", "")),
                    )
                ).lower()
            ),
            None,
        )
        if selected:
            return selected
        if len(accounts) == 1:
            return accounts[0]
        if not accounts:
            raise CommandError("Myfxbook returned no connected accounts. Add IC Markets in Myfxbook first.")
        raise CommandError("Multiple accounts found but IC Markets was not identifiable; rerun with --account ID.")

    def _print_schema(self, label, records):
        if not records:
            self.stdout.write(f"Observed {label} fields: none (the returned list is empty)")
            return
        fields = ", ".join(sorted(records[0].keys()))
        self.stdout.write(f"Observed {label} fields: {fields}")
