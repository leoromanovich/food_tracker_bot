import asyncio
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import add_food
from bot.ui.callbacks import ConditionBoolAction, ConditionWellBeingAction
from bot.fsm.states import FoodLogStates
from bot.services.condition_service import ConditionService
from bot.services.file_store import FileStore
from bot.services.food_event_service import FoodEventService
from bot.services.foods_service import FoodsService


class FakeTimeService:
    def __init__(self):
        self._now = datetime(2025, 3, 12, 19, 30, tzinfo=ZoneInfo("UTC"))

    def now(self):
        return self._now

    def short_id(self, length: int = 8) -> str:
        return "cafebabe"


class StubMessage:
    def __init__(self, text: str = ""):
        self.text = text
        self.replies: list[str] = []

    async def answer(self, text: str, reply_markup=None):
        self.replies.append(text)


class StubCallback:
    def __init__(self, message: StubMessage | None = None):
        self.message = message or StubMessage()
        self.answers: list[str | None] = []

    async def answer(self, text: str | None = None, show_alert: bool = False):
        self.answers.append(text or "")


def _build_state(tmp_path: Path) -> FSMContext:
    file_store = FileStore(tmp_path)
    fake_time = FakeTimeService()
    service = FoodEventService(
        file_store=file_store,
        foods_service=FoodsService(file_store),
        condition_service=ConditionService(file_store),
        time_service=fake_time,
    )
    add_food.setup_dependencies(service, fake_time)

    storage = MemoryStorage()
    return FSMContext(
        storage=storage, key=StorageKey(bot_id=1, chat_id=1, user_id=1)
    )


def test_full_flow_persists_files(tmp_path: Path):
    asyncio.run(_run_flow_test(tmp_path))


async def _run_flow_test(tmp_path: Path):
    state = _build_state(tmp_path)

    start_message = StubMessage("/add")
    await add_food._start_flow(start_message, state)
    assert await state.get_state() == FoodLogStates.adding_foods.state

    user_message = StubMessage("Паста\nСыр")
    await add_food.handle_foods_input(user_message, state)

    finish_callback = StubCallback(StubMessage())
    await add_food.cb_finish(finish_callback, state)

    confirm_callback = StubCallback(StubMessage())
    await add_food.cb_confirm_finish(confirm_callback, state)
    assert await state.get_state() == FoodLogStates.ask_condition_bloating.state

    bloating_callback = StubCallback(StubMessage())
    await add_food.cb_condition_bloating(
        bloating_callback,
        ConditionBoolAction(symptom="bloating", value="yes"),
        state,
    )

    diarrhea_callback = StubCallback(StubMessage())
    await add_food.cb_condition_diarrhea(
        diarrhea_callback,
        ConditionBoolAction(symptom="diarrhea", value="no"),
        state,
    )

    well_being_callback = StubCallback(StubMessage())
    await add_food.cb_condition_well_being(
        well_being_callback, ConditionWellBeingAction(score=6), state
    )

    assert await state.get_state() is None
    food_logs = list((tmp_path / "FoodLog").glob("*.md"))
    condition_logs = list((tmp_path / "ConditionLog").glob("*.md"))
    assert len(food_logs) == 1
    assert len(condition_logs) == 1


def test_empty_foods_input_shows_hint(tmp_path: Path):
    asyncio.run(_run_empty_foods_input_test(tmp_path))


async def _run_empty_foods_input_test(tmp_path: Path) -> None:
    state = _build_state(tmp_path)

    start_message = StubMessage("/add")
    await add_food._start_flow(start_message, state)

    user_message = StubMessage("")
    await add_food.handle_foods_input(user_message, state)

    assert await state.get_state() == FoodLogStates.adding_foods.state
    assert user_message.replies == [
        "Не нашёл текста с ингредиентами. Напишите список строками."
    ]


def test_finish_without_foods_alerts_user(tmp_path: Path):
    asyncio.run(_run_finish_without_foods_test(tmp_path))


async def _run_finish_without_foods_test(tmp_path: Path) -> None:
    state = _build_state(tmp_path)

    start_message = StubMessage("/add")
    await add_food._start_flow(start_message, state)

    finish_callback = StubCallback(StubMessage())
    await add_food.cb_finish(finish_callback, state)

    assert await state.get_state() == FoodLogStates.adding_foods.state
    assert finish_callback.answers == ["Сначала добавьте ингредиенты."]
    assert finish_callback.message.replies == []


def test_cancel_on_bloating_clears_state_and_files(tmp_path: Path):
    asyncio.run(_run_cancel_on_bloating_test(tmp_path))


async def _run_cancel_on_bloating_test(tmp_path: Path) -> None:
    state = _build_state(tmp_path)

    start_message = StubMessage("/add")
    await add_food._start_flow(start_message, state)
    await add_food.handle_foods_input(StubMessage("Паста"), state)
    await add_food.cb_finish(StubCallback(StubMessage()), state)
    await add_food.cb_confirm_finish(StubCallback(StubMessage()), state)

    cancel_callback = StubCallback(StubMessage())
    await add_food.cb_condition_bloating(
        cancel_callback,
        ConditionBoolAction(symptom="bloating", value="cancel"),
        state,
    )

    assert await state.get_state() is None
    assert cancel_callback.message.replies[-1] == (
        "Фиксация отменена. Ничего не сохранено. Нажмите «Добавить еду», "
        "чтобы начать заново."
    )
    assert list((tmp_path / "FoodLog").glob("*.md")) == []
    assert list((tmp_path / "ConditionLog").glob("*.md")) == []


def test_cancel_on_diarrhea_clears_state_and_files(tmp_path: Path):
    asyncio.run(_run_cancel_on_diarrhea_test(tmp_path))


async def _run_cancel_on_diarrhea_test(tmp_path: Path) -> None:
    state = _build_state(tmp_path)

    start_message = StubMessage("/add")
    await add_food._start_flow(start_message, state)
    await add_food.handle_foods_input(StubMessage("Паста"), state)
    await add_food.cb_finish(StubCallback(StubMessage()), state)
    await add_food.cb_confirm_finish(StubCallback(StubMessage()), state)
    await add_food.cb_condition_bloating(
        StubCallback(StubMessage()),
        ConditionBoolAction(symptom="bloating", value="yes"),
        state,
    )

    cancel_callback = StubCallback(StubMessage())
    await add_food.cb_condition_diarrhea(
        cancel_callback,
        ConditionBoolAction(symptom="diarrhea", value="cancel"),
        state,
    )

    assert await state.get_state() is None
    assert cancel_callback.message.replies[-1] == (
        "Фиксация отменена. Ничего не сохранено. Нажмите «Добавить еду», "
        "чтобы начать заново."
    )
    assert list((tmp_path / "FoodLog").glob("*.md")) == []
    assert list((tmp_path / "ConditionLog").glob("*.md")) == []
