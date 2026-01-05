from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Tuple

from app.storage.models import ArbitrageMetric


@dataclass
class ArbitrageResult:
    symbol_std: str
    direction: str
    raw_spread: float
    net_pct: float


@dataclass
class EventState:
    event_id: int | None
    start_ts: datetime
    max_net_pct: float
    sum_net_pct: float
    samples: int


class ArbitrageEngine:
    def __init__(self, fee_map: Dict[str, float], threshold_pct: float) -> None:
        self.fee_map = fee_map
        self.threshold_pct = threshold_pct
        self.events: Dict[Tuple[str, str], EventState] = {}

    def compute(
        self,
        symbol_std: str,
        sell_exchange: str,
        sell_bid: float,
        buy_exchange: str,
        buy_ask: float,
    ) -> ArbitrageResult:
        raw_spread = sell_bid - buy_ask
        sell_fee = self.fee_map.get(sell_exchange, 0.0)
        buy_fee = self.fee_map.get(buy_exchange, 0.0)
        net = sell_bid * (1 - sell_fee) - buy_ask * (1 + buy_fee)
        net_pct = (net / buy_ask) * 100
        direction = f"{sell_exchange}_sell/{buy_exchange}_buy"
        return ArbitrageResult(symbol_std, direction, raw_spread, net_pct)

    def update_event_state(
        self,
        result: ArbitrageResult,
        now: datetime | None = None,
    ) -> tuple[str, EventState | None]:
        now_ts = now or datetime.now(timezone.utc)
        key = (result.symbol_std, result.direction)
        state = self.events.get(key)
        if result.net_pct >= self.threshold_pct:
            if state is None:
                state = EventState(
                    event_id=None,
                    start_ts=now_ts,
                    max_net_pct=result.net_pct,
                    sum_net_pct=result.net_pct,
                    samples=1,
                )
                self.events[key] = state
                return "start", state
            state.max_net_pct = max(state.max_net_pct, result.net_pct)
            state.sum_net_pct += result.net_pct
            state.samples += 1
            return "update", state
        if state is None:
            return "none", None
        state.sum_net_pct += result.net_pct
        state.samples += 1
        return "close", state

    def finalize_event(self, symbol_std: str, direction: str) -> EventState | None:
        return self.events.pop((symbol_std, direction), None)

    @staticmethod
    def to_metric(result: ArbitrageResult, timestamp: datetime) -> ArbitrageMetric:
        return ArbitrageMetric(
            timestamp=timestamp,
            symbol_std=result.symbol_std,
            direction=result.direction,
            raw_spread=result.raw_spread,
            net_pct=result.net_pct,
        )
