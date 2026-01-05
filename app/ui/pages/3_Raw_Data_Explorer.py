from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from app.config import load_settings
from app.storage.repository import Repository


EXPORT_DIR = Path("app/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Raw Data Explorer", layout="wide")
settings = load_settings()
repository = Repository(settings.db_path)

st.title("Raw Data Explorer")

col1, col2, col3, col4 = st.columns(4)
with col1:
    start_date = st.date_input("Başlangıç", datetime.now(timezone.utc).date() - timedelta(days=1))
with col2:
    end_date = st.date_input("Bitiş", datetime.now(timezone.utc).date())
with col3:
    symbol = st.selectbox("Coin", ["All"] + settings.watchlist)
with col4:
    exchange = st.selectbox("Exchange", ["All", "binance", "kraken"])

start_ts = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
end_ts = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

snapshots = repository.list_snapshots(start_ts, end_ts, symbol, exchange)
if snapshots:
    df = pd.DataFrame(
        [
            {
                "timestamp": snap.timestamp,
                "exchange": snap.exchange,
                "symbol": snap.symbol_std,
                "bid": snap.bid,
                "ask": snap.ask,
                "last": snap.last,
                "volume_24h": snap.volume_24h,
                "spread_abs": snap.spread_abs,
                "spread_pct": snap.spread_pct,
            }
            for snap in snapshots
        ]
    )
    st.dataframe(df, use_container_width=True)

    if st.button("CSV Export"):
        file_path = EXPORT_DIR / f"snapshots_{int(datetime.now().timestamp())}.csv"
        df.to_csv(file_path, index=False)
        st.success(f"CSV kaydedildi: {file_path}")
else:
    st.info("Snapshot verisi bulunamadı.")
