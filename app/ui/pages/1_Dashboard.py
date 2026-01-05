from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from app.config import load_settings
from app.core.state import STATE
from app.storage.repository import Repository
from app.ui.service_manager import get_service


st.set_page_config(page_title="Dashboard", layout="wide")
settings = load_settings()
service = get_service(settings)
repository = Repository(settings.db_path)

st.title("Dashboard")

col_status, col_actions = st.columns([2, 1])
with col_status:
    status = STATE.get_status()
    st.subheader("Bağlantı Durumları")
    st.write(
        {
            "Binance": "✅" if status["binance"].connected else "❌",
            "Kraken": "✅" if status["kraken"].connected else "❌",
        }
    )
    st.caption(
        f"Binance: {status['binance'].last_message} | Kraken: {status['kraken'].last_message}"
    )

with col_actions:
    st.subheader("Monitoring")
    if st.button("Start Monitoring", use_container_width=True):
        service.start()
        st.success("Monitoring başlatıldı")
    if st.button("Stop Monitoring", use_container_width=True):
        service.stop()
        st.warning("Monitoring durduruldu")

st.subheader("Seçili Coinler")
st.write(", ".join(settings.watchlist))

prices = STATE.get_prices()
rows = []
for symbol in settings.watchlist:
    binance = prices.get("binance", {}).get(symbol)
    kraken = prices.get("kraken", {}).get(symbol)
    if not binance or not kraken:
        continue
    net_binance_sell = (
        (binance.bid * (1 - settings.binance_fee) - kraken.ask * (1 + settings.kraken_fee))
        / kraken.ask
        * 100
    )
    net_kraken_sell = (
        (kraken.bid * (1 - settings.kraken_fee) - binance.ask * (1 + settings.binance_fee))
        / binance.ask
        * 100
    )
    rows.append(
        {
            "symbol": symbol,
            "binance_bid": binance.bid,
            "binance_ask": binance.ask,
            "kraken_bid": kraken.bid,
            "kraken_ask": kraken.ask,
            "net_pct_binance_sell": net_binance_sell,
            "net_pct_kraken_sell": net_kraken_sell,
            "firsat": "✅"
            if max(net_binance_sell, net_kraken_sell) >= settings.min_net_pct
            else "—",
        }
    )

st.subheader("Canlı Arbitraj Tablosu")
if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
else:
    st.info("Veri bekleniyor...")

st.subheader("Net Spread Trend")
chart_symbol = st.selectbox("Coin", settings.watchlist)
minutes = st.slider("Son kaç dakika", 1, 60, 10)

end_ts = datetime.now(timezone.utc)
start_ts = end_ts - timedelta(minutes=minutes)
metrics = repository.list_metrics(chart_symbol, start_ts, end_ts)
if metrics:
    df = pd.DataFrame(
        [
            {
                "timestamp": metric.timestamp,
                "direction": metric.direction,
                "net_pct": metric.net_pct,
            }
            for metric in metrics
        ]
    )
    fig = px.line(df, x="timestamp", y="net_pct", color="direction")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Grafik için yeterli veri yok.")

components.html(
    "<script>setTimeout(function(){window.location.reload();}, 1000);</script>",
    height=0,
)
