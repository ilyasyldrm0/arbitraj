from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Dict

import websockets

from app.core.state import PriceData, SharedState

logger = logging.getLogger(__name__)


class BinanceCollector:
    def __init__(
        self,
        symbols_map: Dict[str, str],
        state: SharedState,
        stop_event: threading.Event | None = None,
    ) -> None:
        self.symbols_map = symbols_map
        self.state = state
        self.stop_event = stop_event
        self._reverse_map = {value.upper(): key for key, value in symbols_map.items()}
        self._last_values: Dict[str, PriceData] = {}

    async def run(self) -> None:
        backoff = 1
        while not self._is_stopped():
            stream_url = self._build_stream_url()
            try:
                self.state.set_status("binance", False, "connecting")
                async with websockets.connect(
                    stream_url, ping_interval=20, ping_timeout=20
                ) as websocket:
                    self.state.set_status("binance", True, "connected")
                    backoff = 1
                    async for message in websocket:
                        if self._is_stopped():
                            break
                        self._handle_message(message)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Binance websocket error: %s", exc)
                self.state.set_status("binance", False, str(exc))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    def _build_stream_url(self) -> str:
        streams = []
        for symbol in self.symbols_map.values():
            stream_symbol = symbol.lower()
            streams.append(f"{stream_symbol}@bookTicker")
            streams.append(f"{stream_symbol}@miniTicker")
        stream_path = "/".join(streams)
        return f"wss://stream.binance.com:9443/stream?streams={stream_path}"

    def _handle_message(self, message: str) -> None:
        payload = json.loads(message)
        data = payload.get("data", {})
        event_type = data.get("e")
        symbol = data.get("s")
        if not symbol:
            return
        symbol_std = self._reverse_map.get(symbol.upper())
        if not symbol_std:
            return
        if event_type == "bookTicker":
            bid = float(data.get("b", 0))
            ask = float(data.get("a", 0))
            last_data = self._last_values.get(symbol_std, PriceData(bid=bid, ask=ask))
            last = last_data.last
            volume = last_data.volume_24h
            price = PriceData(bid=bid, ask=ask, last=last, volume_24h=volume)
            self._last_values[symbol_std] = price
            self.state.update_price("binance", symbol_std, price)
        elif event_type == "24hrMiniTicker":
            last = float(data.get("c", 0))
            volume = float(data.get("v", 0))
            last_data = self._last_values.get(symbol_std, PriceData(bid=0, ask=0))
            price = PriceData(
                bid=last_data.bid,
                ask=last_data.ask,
                last=last,
                volume_24h=volume,
            )
            self._last_values[symbol_std] = price
            if price.bid and price.ask:
                self.state.update_price("binance", symbol_std, price)

    def _is_stopped(self) -> bool:
        return bool(self.stop_event and self.stop_event.is_set())
