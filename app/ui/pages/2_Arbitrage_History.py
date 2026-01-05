from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from app.config import load_settings
from app.storage.repository import Repository


EXPORT_DIR = Path("app/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Arbitrage History", layout="wide")
settings = load_settings()
repository = Repository(settings.db_path)

st.title("Arbitrage History")

col1, col2, col3, col4 = st.columns(4)
with col1:
    start_date = st.date_input("Başlangıç", datetime.now(timezone.utc).date() - timedelta(days=1))
with col2:
    end_date = st.date_input("Bitiş", datetime.now(timezone.utc).date())
with col3:
    symbol = st.selectbox("Coin", ["All"] + settings.watchlist)
with col4:
    direction = st.selectbox(
        "Direction",
        ["All", "binance_sell/kraken_buy", "kraken_sell/binance_buy"],
    )

min_net_pct = st.number_input("Min Net %", min_value=0.0, value=settings.min_net_pct)

start_ts = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
end_ts = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

events = repository.list_events(start_ts, end_ts, symbol, direction, min_net_pct)
if events:
    df = pd.DataFrame(
        [
            {
                "id": event.id,
                "symbol": event.symbol_std,
                "direction": event.direction,
                "start": event.start_ts,
                "end": event.end_ts,
                "status": event.status,
                "max_net_pct": event.max_net_pct,
                "avg_net_pct": event.avg_net_pct,
                "duration_s": event.duration_s,
            }
            for event in events
        ]
    )
    st.dataframe(df, use_container_width=True)

    if st.button("CSV Export"):
        file_path = EXPORT_DIR / f"arbitrage_events_{int(datetime.now().timestamp())}.csv"
        df.to_csv(file_path, index=False)
        st.success(f"CSV kaydedildi: {file_path}")

    if st.button("PDF Export (Opsiyonel)"):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            file_path = EXPORT_DIR / f"arbitrage_events_{int(datetime.now().timestamp())}.pdf"
            c = canvas.Canvas(str(file_path), pagesize=letter)
            text = c.beginText(40, 750)
            text.textLine("Arbitrage Events Report")
            for _, row in df.iterrows():
                text.textLine(
                    f"{row['symbol']} | {row['direction']} | max {row['max_net_pct']:.2f}%"
                )
            c.drawText(text)
            c.save()
            st.success(f"PDF kaydedildi: {file_path}")
        except Exception as exc:  # noqa: BLE001
            st.warning(f"PDF export başarısız: {exc}")
else:
    st.info("Seçilen kriterlerde event bulunamadı.")
