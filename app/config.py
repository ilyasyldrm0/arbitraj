from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_SETTINGS_PATH = Path("app/data/settings.json")
DEFAULT_DB_PATH = Path("app/data/app.db")


@dataclass
class Settings:
    watchlist: List[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    snapshot_interval_s: int = 1
    binance_fee: float = 0.001
    kraken_fee: float = 0.0026
    min_net_pct: float = 0.2
    db_path: str = str(DEFAULT_DB_PATH)
    mapping_overrides: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "watchlist": self.watchlist,
            "snapshot_interval_s": self.snapshot_interval_s,
            "binance_fee": self.binance_fee,
            "kraken_fee": self.kraken_fee,
            "min_net_pct": self.min_net_pct,
            "db_path": self.db_path,
            "mapping_overrides": self.mapping_overrides,
        }


def load_settings(path: Path | None = None) -> Settings:
    settings_path = path or DEFAULT_SETTINGS_PATH
    if not settings_path.exists():
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = Settings()
        save_settings(settings, settings_path)
        return settings
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    return Settings(
        watchlist=data.get("watchlist", ["BTC/USDT", "ETH/USDT"]),
        snapshot_interval_s=int(data.get("snapshot_interval_s", 1)),
        binance_fee=float(data.get("binance_fee", 0.001)),
        kraken_fee=float(data.get("kraken_fee", 0.0026)),
        min_net_pct=float(data.get("min_net_pct", 0.2)),
        db_path=str(data.get("db_path", DEFAULT_DB_PATH)),
        mapping_overrides=data.get("mapping_overrides", {}),
    )


def save_settings(settings: Settings, path: Path | None = None) -> None:
    settings_path = path or DEFAULT_SETTINGS_PATH
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
