"""
MT5 history parsers.

All parsers return a list of normalised trade dicts with these keys:
    mt5_ticket, symbol, direction, volume, entry_price, exit_price,
    sl, tp, entry_time, exit_time, profit, commission, swap

A future LiveMT5Adapter (MetaTrader5 package, Windows) implements the same
`parse()` contract (see api/mt5/client.py), so the importer code never changes.
"""

from .base import MT5Parser
from .csv_parser import CsvParser

__all__ = ["MT5Parser", "CsvParser"]
