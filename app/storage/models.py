from __future__ import annotations

from datetime import datetime
from sqlalchemy import Float, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.db import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    exchange: Mapped[str] = mapped_column(String(20), index=True)
    symbol_std: Mapped[str] = mapped_column(String(20), index=True)
    bid: Mapped[float] = mapped_column(Float)
    ask: Mapped[float] = mapped_column(Float)
    last: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    spread_abs: Mapped[float] = mapped_column(Float)
    spread_pct: Mapped[float] = mapped_column(Float)


class ArbitrageEvent(Base):
    __tablename__ = "arbitrage_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_std: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(40), index=True)
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="open", index=True)
    max_net_pct: Mapped[float] = mapped_column(Float)
    avg_net_pct: Mapped[float] = mapped_column(Float)
    duration_s: Mapped[int] = mapped_column(Integer, default=0)


class ArbitrageMetric(Base):
    __tablename__ = "arbitrage_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    symbol_std: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(40), index=True)
    raw_spread: Mapped[float] = mapped_column(Float)
    net_pct: Mapped[float] = mapped_column(Float)
