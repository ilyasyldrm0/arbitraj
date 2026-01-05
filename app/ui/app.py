from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPT_DIR) in sys.path:
    sys.path.remove(str(SCRIPT_DIR))
if "app" in sys.modules:
    module = sys.modules["app"]
    module_path = Path(getattr(module, "__file__", "")).resolve()
    if not hasattr(module, "__path__") or module_path == Path(__file__).resolve():
        del sys.modules["app"]

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

if __name__ == "__main__":
    print("Başlatma kontrolü: ayarlar yüklendi ->", settings)
    print("Streamlit ile çalıştırmak için: streamlit run app/ui/app.py")
    # Do not spawn another Streamlit process from here. Streamlit itself runs
    # this script and rerunning it via subprocess causes recursive starts
    # that create multiple server instances and repeated restarts.
    raise SystemExit(0)
