from __future__ import annotations

import time

from app.config import load_settings
from app.core.scheduler import MonitoringService
from app.logging_config import setup_logging


def main() -> None:
    setup_logging()
    settings = load_settings()
    service = MonitoringService(settings)
    service.start()
    print("Collector running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()


if __name__ == "__main__":
    main()
