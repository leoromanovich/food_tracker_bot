from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    bot_token: str
    data_dir: Path
    timezone: ZoneInfo


def load_settings() -> Settings:
    load_dotenv()

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in environment")

    data_dir = Path(os.environ.get("DATA_DIR", "./data")).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    tz_name = os.environ.get("TZ", "UTC")
    try:
        timezone = ZoneInfo(tz_name)
    except Exception as exc:  # pragma: no cover - invalid tz should be obvious
        raise RuntimeError(f"Invalid timezone '{tz_name}': {exc}") from exc

    return Settings(bot_token=token, data_dir=data_dir, timezone=timezone)
