from __future__ import annotations

import json

import streamlit as st

from app.config import Settings, load_settings, save_settings


st.set_page_config(page_title="Settings", layout="wide")
settings = load_settings()

st.title("Settings")

watchlist = st.multiselect(
    "Watchlist",
    options=["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"],
    default=settings.watchlist,
)

col1, col2, col3 = st.columns(3)
with col1:
    binance_fee = st.number_input("Binance Fee (%)", value=settings.binance_fee * 100, step=0.01)
with col2:
    kraken_fee = st.number_input("Kraken Fee (%)", value=settings.kraken_fee * 100, step=0.01)
with col3:
    min_net_pct = st.number_input("Min Net %", value=settings.min_net_pct, step=0.01)

snapshot_interval = st.number_input(
    "Snapshot Interval (s)", min_value=1, value=settings.snapshot_interval_s
)

db_path = st.text_input("DB Path", value=settings.db_path)

mapping_text = st.text_area(
    "Mapping Overrides (JSON)", value=json.dumps(settings.mapping_overrides, indent=2), height=200
)

if st.button("Save Settings"):
    try:
        overrides = json.loads(mapping_text) if mapping_text.strip() else {}
    except json.JSONDecodeError as exc:
        st.error(f"JSON hatası: {exc}")
    else:
        new_settings = Settings(
            watchlist=watchlist or settings.watchlist,
            snapshot_interval_s=int(snapshot_interval),
            binance_fee=binance_fee / 100,
            kraken_fee=kraken_fee / 100,
            min_net_pct=float(min_net_pct),
            db_path=db_path,
            mapping_overrides=overrides,
        )
        save_settings(new_settings)
        st.success("Ayarlar kaydedildi. İzlemeyi yeniden başlatın.")
