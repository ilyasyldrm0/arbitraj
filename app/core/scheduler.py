from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import List

from app.collectors.binance import BinanceCollector
from app.collectors.kraken import KrakenCollector
from app.config import Settings
from app.core.arbitrage import ArbitrageEngine
from app.core.state import STATE, PriceData
from app.core.symbol_mapping import SymbolMapping
from app.logging_config import setup_logging
from app.storage.db import Base, get_engine
from app.storage.models import ArbitrageMetric, Snapshot
from app.storage.repository import Repository

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_thread, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)

    def _run_thread(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        setup_logging()
        logger.info("Monitoring service starting")
        engine = get_engine(self.settings.db_path)
        Base.metadata.create_all(engine)
        repository = Repository(self.settings.db_path)

        mapping = SymbolMapping(self.settings.mapping_overrides)
        exchange_map = mapping.as_exchange_map(self.settings.watchlist)

        binance = BinanceCollector(exchange_map["binance"], STATE, self.stop_event)
        kraken = KrakenCollector(exchange_map["kraken"], STATE, self.stop_event)
        arbitrage_engine = ArbitrageEngine(
            fee_map={
                "binance": self.settings.binance_fee,
                "kraken": self.settings.kraken_fee,
            },
            threshold_pct=self.settings.min_net_pct,
        )

        tasks = [
            asyncio.create_task(binance.run()),
            asyncio.create_task(kraken.run()),
            asyncio.create_task(self._snapshot_loop(repository, arbitrage_engine)),
        ]

        try:
            while not self.stop_event.is_set():
                await asyncio.sleep(0.5)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("Monitoring service stopped")

    async def _snapshot_loop(
        self,
        repository: Repository,
        arbitrage_engine: ArbitrageEngine,
    ) -> None:
        interval = max(1, int(self.settings.snapshot_interval_s))
        while not self.stop_event.is_set():
            now = datetime.now(timezone.utc).replace(microsecond=0)
            prices = STATE.get_prices()
            snapshots: list[Snapshot] = []
            for exchange, symbols in prices.items():
                for symbol_std, data in symbols.items():
                    snapshots.append(self._build_snapshot(now, exchange, symbol_std, data))
            if snapshots:
                repository.add_snapshots(snapshots)
            metrics = self._process_arbitrage(now, prices, arbitrage_engine, repository)
            if metrics:
                repository.add_metrics(metrics)
            await asyncio.sleep(interval)

    def _build_snapshot(
        self,
        timestamp: datetime,
        exchange: str,
        symbol_std: str,
        data: PriceData,
    ) -> Snapshot:
        spread_abs = data.ask - data.bid
        spread_pct = (spread_abs / data.bid * 100) if data.bid else 0.0
        return Snapshot(
            timestamp=timestamp,
            exchange=exchange,
            symbol_std=symbol_std,
            bid=data.bid,
            ask=data.ask,
            last=data.last,
            volume_24h=data.volume_24h,
            spread_abs=spread_abs,
            spread_pct=spread_pct,
        )

    def _process_arbitrage(
        self,
        timestamp: datetime,
        prices: dict[str, dict[str, PriceData]],
        arbitrage_engine: ArbitrageEngine,
        repository: Repository,
    ) -> List[ArbitrageMetric]:
        metrics: List[ArbitrageMetric] = []
        for symbol in self.settings.watchlist:
            binance_data = prices.get("binance", {}).get(symbol)
            kraken_data = prices.get("kraken", {}).get(symbol)
            if not binance_data or not kraken_data:
                continue
            directions = [
                ("binance", binance_data.bid, "kraken", kraken_data.ask),
                ("kraken", kraken_data.bid, "binance", binance_data.ask),
            ]
            for sell_exchange, sell_bid, buy_exchange, buy_ask in directions:
                result = arbitrage_engine.compute(
                    symbol, sell_exchange, sell_bid, buy_exchange, buy_ask
                )
                metrics.append(arbitrage_engine.to_metric(result, timestamp))
                action, state = arbitrage_engine.update_event_state(result, timestamp)
                if action == "start" and state:
                    event = repository.create_event(
                        symbol_std=result.symbol_std,
                        direction=result.direction,
                        start_ts=state.start_ts,
                        max_net_pct=state.max_net_pct,
                        avg_net_pct=state.sum_net_pct / state.samples,
                    )
                    state.event_id = event.id
                elif action == "close" and state:
                    avg = state.sum_net_pct / state.samples
                    duration = int((timestamp - state.start_ts).total_seconds())
                    if state.event_id is not None:
                        repository.close_event(
                            state.event_id,
                            timestamp,
                            state.max_net_pct,
                            avg,
                            duration,
                        )
                    arbitrage_engine.finalize_event(result.symbol_std, result.direction)
        return metrics
