from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


DEFAULT_KRAKEN_OVERRIDES = {
    "BTC/USDT": "XBT/USDT",
    "ETH/USDT": "ETH/USDT",
    "SOL/USDT": "SOL/USDT",
    "XRP/USDT": "XRP/USDT",
    "ADA/USDT": "ADA/USDT",
}


@dataclass
class SymbolMapping:
    overrides: Dict[str, Dict[str, str]]

    def to_binance(self, symbol_std: str) -> str:
        override = self.overrides.get("binance", {}).get(symbol_std)
        if override:
            return override
        return symbol_std.replace("/", "")

    def to_kraken(self, symbol_std: str) -> str:
        override = self.overrides.get("kraken", {}).get(symbol_std)
        if override:
            return override
        if symbol_std in DEFAULT_KRAKEN_OVERRIDES:
            return DEFAULT_KRAKEN_OVERRIDES[symbol_std]
        base, quote = symbol_std.split("/")
        if base == "BTC":
            base = "XBT"
        return f"{base}/{quote}"

    def as_exchange_map(self, symbols: list[str]) -> Dict[str, Dict[str, str]]:
        return {
            "binance": {symbol: self.to_binance(symbol) for symbol in symbols},
            "kraken": {symbol: self.to_kraken(symbol) for symbol in symbols},
        }
