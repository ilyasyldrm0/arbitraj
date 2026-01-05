from __future__ import annotations

from app.config import DEFAULT_DB_PATH, load_settings
from app.storage.db import Base, get_engine
from app.storage import models  # noqa: F401


def main() -> None:
    settings = load_settings()
    db_path = settings.db_path or str(DEFAULT_DB_PATH)
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    main()
