import asyncio
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from bot.domain.models import Condition, FoodEventDraft
from bot.services.condition_service import ConditionService
from bot.services.file_store import FileStore
from bot.services.food_event_service import FoodEventService
from bot.services.foods_service import FoodsService


class FixedTimeService:
    def __init__(self):
        self._now = datetime(2025, 3, 12, 19, 30, tzinfo=ZoneInfo("UTC"))

    def now(self):
        return self._now

    def short_id(self, length: int = 8) -> str:  # pragma: no cover - deterministic
        return "deadbeef"


def test_food_event_persists_markdown(tmp_path: Path):
    asyncio.run(_run_persist_test(tmp_path))


async def _run_persist_test(tmp_path: Path):
    file_store = FileStore(tmp_path)
    service = FoodEventService(
        file_store=file_store,
        foods_service=FoodsService(file_store),
        condition_service=ConditionService(file_store),
        time_service=FixedTimeService(),
    )
    draft = FoodEventDraft(started_at=datetime.now(), foods_raw=["Паста", "Сыр", "паста"])
    condition = Condition(bloating=True, diarrhea=False, well_being=6)

    result = await service.persist_event(draft, condition)

    food_log_content = Path(result.food_log_path).read_text(encoding="utf-8")
    condition_log_content = Path(result.condition_log_path).read_text(encoding="utf-8")

    assert "---" in food_log_content
    assert "[[паста]]" in food_log_content
    assert "symptoms" in condition_log_content
