"""
Live MT5 integration (placeholder).

The `MetaTrader5` Python package connects to a locally running MT5 terminal
(Windows). A future LiveMT5Adapter implements the same `parse()` contract as
the file parsers in api.mt5.parsers, so app.imports.services.import_rows works
unchanged whether rows come from a CSV upload or a live terminal.

Sketch (not active — requires the terminal + MetaTrader5 package on Windows):

    import MetaTrader5 as mt5
    mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER)
    deals = mt5.history_deals_get(from_date, to_date)
    # normalise each deal into the dict shape documented in parsers/__init__.py

Credentials are never stored by this app; they would be supplied at sync time.
"""
