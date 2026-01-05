from __future__ import annotations

import streamlit as st

from app.config import Settings
from app.core.scheduler import MonitoringService


@st.cache_resource
def get_service(settings: Settings) -> MonitoringService:
    return MonitoringService(settings)
