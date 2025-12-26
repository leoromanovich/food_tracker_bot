import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from bot.services.breath_reminder_service import BreathReminderService
from bot.services.condition_service import ConditionService
from bot.services.file_store import FileStore


def test_persist_breath_overwrites_same_day(tmp_path):
    service = ConditionService(FileStore(tmp_path))
    timestamp = datetime(2025, 3, 12, 7, 0, tzinfo=ZoneInfo("UTC"))

    asyncio.run(service.persist_breath(timestamp, "strong"))
    asyncio.run(service.persist_breath(timestamp, "none"))

    target = tmp_path / "ConditionLog" / "2025-03-12_breath.md"
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "breath_smell: none" in content
    assert "breath_smell: strong" not in content


def test_breath_reminder_service_due_logic(tmp_path):
    asyncio.run(_run_reminder_due_test(tmp_path))


async def _run_reminder_due_test(tmp_path):
    service = BreathReminderService(FileStore(tmp_path))
    await service.add_or_update(user_id=1, chat_id=2, time_str="07:00")

    due = await service.get_due("07:00", "2025-03-12")
    assert len(due) == 1

    await service.mark_sent(due[0], "2025-03-12")
    due_again = await service.get_due("07:00", "2025-03-12")
    assert due_again == []

    await service.add_or_update(user_id=2, chat_id=3, time_str="2025-03-12_07:00:20", one_shot=True)
    due_one_shot = await service.get_due_one_shot("2025-03-12_07:00:25")
    assert len(due_one_shot) == 1
    await service.mark_sent(due_one_shot[0], "2025-03-12")
    assert await service.get_due_one_shot("2025-03-12_07:00:30") == []
