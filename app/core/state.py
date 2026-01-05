from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict


@dataclass
class PriceData:
    bid: float
    ask: float
    last: float | None = None
    volume_24h: float | None = None


@dataclass
class ConnectionStatus:
    connected: bool = False
    last_message: str | None = None


@dataclass
class SharedState:
    prices: Dict[str, Dict[str, PriceData]] = field(default_factory=dict)
    status: Dict[str, ConnectionStatus] = field(
        default_factory=lambda: {"binance": ConnectionStatus(), "kraken": ConnectionStatus()}
    )
    lock: Lock = field(default_factory=Lock)

    def update_price(self, exchange: str, symbol_std: str, data: PriceData) -> None:
        with self.lock:
            self.prices.setdefault(exchange, {})[symbol_std] = data

    def get_prices(self) -> Dict[str, Dict[str, PriceData]]:
        with self.lock:
            return {ex: prices.copy() for ex, prices in self.prices.items()}

    def set_status(self, exchange: str, connected: bool, message: str | None = None) -> None:
        with self.lock:
            status = self.status.setdefault(exchange, ConnectionStatus())
            status.connected = connected
            status.last_message = message

    def get_status(self) -> Dict[str, ConnectionStatus]:
        with self.lock:
            return {ex: ConnectionStatus(s.connected, s.last_message) for ex, s in self.status.items()}


STATE = SharedState()
