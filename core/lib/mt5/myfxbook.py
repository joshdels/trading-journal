"""Small read-only client for Myfxbook's documented JSON API.

Credentials are exchanged for an IP-bound session and are never persisted.
This module intentionally contains no database or trade-execution behavior.
"""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://www.myfxbook.com/api"


class MyfxbookError(RuntimeError):
    pass


class MyfxbookConnector:
    """Official Myfxbook personal-account endpoints used by the journal."""

    def __init__(self, email=None, password=None, timeout=30):
        self.email = email
        self.password = password
        self.timeout = timeout
        self.session = None

    def _get(self, endpoint, **params):
        url = f"{BASE_URL}/{endpoint}.json?{urlencode(params)}"
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "TradingJournal/1.0"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read())
        except HTTPError as exc:
            raise MyfxbookError(f"Myfxbook HTTP {exc.code}") from exc
        except (URLError, json.JSONDecodeError) as exc:
            raise MyfxbookError(f"Myfxbook is unreachable: {exc}") from exc
        if not isinstance(result, dict):
            raise MyfxbookError("Myfxbook returned an unexpected response.")
        if result.get("error"):
            raise MyfxbookError(result.get("message") or "Myfxbook API error")
        return result

    def authenticate(self, email=None, password=None):
        email = email or self.email
        password = password or self.password
        if not email or not password:
            raise MyfxbookError("MYFXBOOK_EMAIL and MYFXBOOK_PASSWORD are required.")
        self.session = self._get("login", email=email, password=password)["session"]
        return self.session

    def _require_session(self):
        if not self.session:
            raise MyfxbookError("Authenticate with Myfxbook first.")
        return self.session

    def get_accounts(self):
        return self._get("get-my-accounts", session=self._require_session()).get("accounts", [])

    def get_open_trades(self, account_id):
        return self._get("get-open-trades", session=self._require_session(), id=account_id).get("openTrades", [])

    def get_open_orders(self, account_id):
        return self._get("get-open-orders", session=self._require_session(), id=account_id).get("openOrders", [])

    def get_history(self, account_id):
        return self._get("get-history", session=self._require_session(), id=account_id).get("history", [])

    def get_daily_gain(self, account_id, start, end):
        return self._get(
            "get-daily-gain",
            session=self._require_session(),
            id=account_id,
            start=start,
            end=end,
        ).get("dailyGain", [])

    def logout(self, session=None):
        if session:
            self.session = session
        if not self.session:
            return None
        try:
            return self._get("logout", session=self.session)
        finally:
            self.session = None

    # Compatibility with the existing, not-yet-finalized journal prototype.
    def login(self, email, password):
        return self.authenticate(email, password)

    def accounts(self, session):
        self.session = session
        return self.get_accounts()

    def open_trades(self, session, account_id):
        self.session = session
        return self.get_open_trades(account_id)

    def history(self, session, account_id):
        self.session = session
        return self.get_history(account_id)

    def logout_session(self, session):
        self.session = session
        return self.logout()


MyfxbookClient = MyfxbookConnector
