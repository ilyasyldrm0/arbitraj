from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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


def _run_streamlit() -> int:
    streamlit_command = [sys.executable, "-m", "streamlit", "run", str(Path(__file__))]
    return_code = 0
    try:
        import subprocess

        return_code = subprocess.call(streamlit_command)
    except FileNotFoundError:
        print("Streamlit bulunamadı. Lütfen `pip install -r requirements.txt` çalıştırın.")
        return_code = 1
    return return_code


if __name__ == "__main__":
    print("Başlatma kontrolü: ayarlar yüklendi ->", settings)
    print("Streamlit ile çalıştırmak için: streamlit run app/ui/app.py")
    raise SystemExit(_run_streamlit())
