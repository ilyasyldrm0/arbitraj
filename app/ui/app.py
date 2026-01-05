from __future__ import annotations

import streamlit as st

from app.config import load_settings
from app.logging_config import setup_logging


setup_logging()
settings = load_settings()

st.set_page_config(page_title="Arbitraj Dashboard", layout="wide")

st.title("Arbitraj Monitoring")
st.markdown(
    "Sol menüden sayfaları seçerek canlı izleme, geçmiş raporlar ve ayarları yönetin."
)

st.info(
    "İzlemeyi başlatmak için Dashboard sayfasındaki Start Monitoring düğmesine basın."
)
