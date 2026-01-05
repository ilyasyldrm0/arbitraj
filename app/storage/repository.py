from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Iterable

from sqlalchemy import select

from app.storage.db import get_session_factory
from app.storage.models import ArbitrageEvent, ArbitrageMetric, Snapshot


class Repository:
    def __init__(self, db_path: str) -> None:
        self._session_factory = get_session_factory(db_path)

    @contextmanager
    def session_scope(self):
        session = self._session_factory()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    def add_snapshots(self, snapshots: Iterable[Snapshot]) -> None:
        with self.session_scope() as session:
            session.add_all(list(snapshots))

    def add_metrics(self, metrics: Iterable[ArbitrageMetric]) -> None:
        with self.session_scope() as session:
            session.add_all(list(metrics))

    def create_event(
        self,
        symbol_std: str,
        direction: str,
        start_ts: datetime,
        max_net_pct: float,
        avg_net_pct: float,
    ) -> ArbitrageEvent:
        with self.session_scope() as session:
            event = ArbitrageEvent(
                symbol_std=symbol_std,
                direction=direction,
                start_ts=start_ts,
                max_net_pct=max_net_pct,
                avg_net_pct=avg_net_pct,
                duration_s=0,
                status="open",
            )
            session.add(event)
            session.flush()
            session.refresh(event)
            return event

    def close_event(
        self,
        event_id: int,
        end_ts: datetime,
        max_net_pct: float,
        avg_net_pct: float,
        duration_s: int,
    ) -> None:
        with self.session_scope() as session:
            event = session.get(ArbitrageEvent, event_id)
            if not event:
                return
            event.end_ts = end_ts
            event.status = "closed"
            event.max_net_pct = max_net_pct
            event.avg_net_pct = avg_net_pct
            event.duration_s = duration_s

    def list_events(
        self,
        start_ts: datetime,
        end_ts: datetime,
        symbol_std: str | None = None,
        direction: str | None = None,
        min_net_pct: float | None = None,
    ) -> list[ArbitrageEvent]:
        with self.session_scope() as session:
            query = select(ArbitrageEvent).where(
                ArbitrageEvent.start_ts >= start_ts,
                ArbitrageEvent.start_ts <= end_ts,
            )
            if symbol_std and symbol_std != "All":
                query = query.where(ArbitrageEvent.symbol_std == symbol_std)
            if direction and direction != "All":
                query = query.where(ArbitrageEvent.direction == direction)
            if min_net_pct is not None:
                query = query.where(ArbitrageEvent.max_net_pct >= min_net_pct)
            return list(session.scalars(query).all())

    def list_snapshots(
        self,
        start_ts: datetime,
        end_ts: datetime,
        symbol_std: str | None = None,
        exchange: str | None = None,
    ) -> list[Snapshot]:
        with self.session_scope() as session:
            query = select(Snapshot).where(
                Snapshot.timestamp >= start_ts,
                Snapshot.timestamp <= end_ts,
            )
            if symbol_std and symbol_std != "All":
                query = query.where(Snapshot.symbol_std == symbol_std)
            if exchange and exchange != "All":
                query = query.where(Snapshot.exchange == exchange)
            return list(session.scalars(query).all())

    def list_metrics(
        self,
        symbol_std: str,
        start_ts: datetime,
        end_ts: datetime,
    ) -> list[ArbitrageMetric]:
        with self.session_scope() as session:
            query = select(ArbitrageMetric).where(
                ArbitrageMetric.symbol_std == symbol_std,
                ArbitrageMetric.timestamp >= start_ts,
                ArbitrageMetric.timestamp <= end_ts,
            )
            return list(session.scalars(query).all())
