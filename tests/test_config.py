from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from bot.config import load_settings


def test_load_settings_reads_data_dir_and_timezone(monkeypatch, tmp_path: Path):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("BOT_TOKEN", "token-value")
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("TZ", "Europe/Moscow")

    settings = load_settings(use_dotenv=False)

    assert settings.data_dir == data_dir.resolve()
    assert settings.data_dir.exists()
    assert settings.timezone == ZoneInfo("Europe/Moscow")


def test_load_settings_requires_bot_token(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="BOT_TOKEN is not set in environment"):
        load_settings(use_dotenv=False)

