"""
MT5 history parsers.

All parsers return a list of normalised trade dicts with these keys:
    mt5_ticket, symbol, direction, volume, entry_price, exit_price,
    sl, tp, entry_time, exit_time, profit, commission, swap

The live webhook normalises the same fields through the local MT5 library, so
the importer and live bridge share one data contract.
"""

from .base import MT5Parser
from .csv_parser import CsvParser

__all__ = ["MT5Parser", "CsvParser"]
