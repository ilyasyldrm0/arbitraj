from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Dict

import websockets
from websockets import WebSocketClientProtocol

from app.core.state import PriceData, SharedState

logger = logging.getLogger(__name__)


class KrakenCollector:
    def __init__(
        self,
        symbols_map: Dict[str, str],
        state: SharedState,
        stop_event: threading.Event | None = None,
    ) -> None:
        self.symbols_map = symbols_map
        self.state = state
        self.stop_event = stop_event
        self._reverse_map = {value: key for key, value in symbols_map.items()}

    async def run(self) -> None:
        backoff = 1
        while not self._is_stopped():
            try:
                self.state.set_status("kraken", False, "connecting")
                async with websockets.connect(
                    "wss://ws.kraken.com", ping_interval=20, ping_timeout=20
                ) as websocket:
                    self.state.set_status("kraken", True, "connected")
                    backoff = 1
                    await self._subscribe(websocket)
                    async for message in websocket:
                        if self._is_stopped():
                            break
                        self._handle_message(message)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Kraken websocket error: %s", exc)
                self.state.set_status("kraken", False, str(exc))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    async def _subscribe(self, websocket: WebSocketClientProtocol) -> None:
        pairs = list(self.symbols_map.values())
        payload = {
            "event": "subscribe",
            "pair": pairs,
            "subscription": {"name": "ticker"},
        }
        await websocket.send(json.dumps(payload))

    def _handle_message(self, message: str) -> None:
        payload = json.loads(message)
        if isinstance(payload, dict):
            return
        if not isinstance(payload, list) or len(payload) < 4:
            return
        data = payload[1]
        pair = payload[-1]
        symbol_std = self._reverse_map.get(pair)
        if not symbol_std:
            return
        bid = float(data.get("b", [0])[0])
        ask = float(data.get("a", [0])[0])
        last = float(data.get("c", [0])[0])
        volume = float(data.get("v", [0])[1]) if data.get("v") else None
        price = PriceData(bid=bid, ask=ask, last=last, volume_24h=volume)
        self.state.update_price("kraken", symbol_std, price)

    def _is_stopped(self) -> bool:
        return bool(self.stop_event and self.stop_event.is_set())
