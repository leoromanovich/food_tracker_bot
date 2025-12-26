from __future__ import annotations

from typing import List

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..domain.models import Condition, ConditionDraft, FoodEventDraft
from ..fsm.states import FoodLogStates
from ..services.food_event_service import FoodEventService
from ..services.time_service import TimeService
from ..ui.callbacks import AddFlowAction, ConditionBoolAction, ConditionWellBeingAction
from ..ui.keyboards import (
    adding_foods_keyboard,
    condition_bool_keyboard,
    condition_well_being_keyboard,
    confirm_finish_keyboard,
    start_keyboard,
)

router = Router()

_food_event_service_instance: FoodEventService | None = None
_time_service_instance: TimeService | None = None


def setup_dependencies(
    food_event_service: FoodEventService, time_service: TimeService
) -> None:
    global _food_event_service_instance, _time_service_instance
    _food_event_service_instance = food_event_service
    _time_service_instance = time_service


def _food_event_service() -> FoodEventService:
    if _food_event_service_instance is None:  # pragma: no cover - wiring issue
        raise RuntimeError("FoodEventService is not configured")
    return _food_event_service_instance


def _time_service() -> TimeService:
    if _time_service_instance is None:  # pragma: no cover - wiring issue
        raise RuntimeError("TimeService is not configured")
    return _time_service_instance


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    await _start_flow(message, state)


@router.callback_query(AddFlowAction.filter(F.action == "start"))
async def cb_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await _start_flow(callback.message, state)


async def _start_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    draft = FoodEventDraft(started_at=_time_service().now())
    await state.update_data(draft=draft.model_dump())
    await state.set_state(FoodLogStates.adding_foods)
    await message.answer(
        "Введите ингредиенты, каждый с новой строки. "
        "После этого используйте кнопки ниже, чтобы завершить или продолжить.",
        reply_markup=adding_foods_keyboard(),
    )


@router.message(FoodLogStates.adding_foods)
async def handle_foods_input(message: Message, state: FSMContext) -> None:
    foods = _extract_lines(message.text or "")
    if not foods:
        await message.answer(
            "Не нашёл текста с ингредиентами. Напишите список строками.",
            reply_markup=adding_foods_keyboard(),
        )
        return

    draft = await _get_draft(state)
    draft.append_foods(foods)
    await state.update_data(draft=draft.model_dump())

    preview = "\n".join(f"• {item}" for item in draft.foods_raw[-5:])
    await message.answer(
        f"Добавил {len(foods)} позиций. Всего: {len(draft.foods_raw)}.\n{preview}",
        reply_markup=adding_foods_keyboard(),
    )


@router.callback_query(FoodLogStates.adding_foods, AddFlowAction.filter(F.action == "continue"))
async def cb_continue(callback: CallbackQuery) -> None:
    await callback.answer("Продолжайте вводить ингредиенты.")


@router.callback_query(FoodLogStates.adding_foods, AddFlowAction.filter(F.action == "finish"))
async def cb_finish(callback: CallbackQuery, state: FSMContext) -> None:
    draft = await _get_draft(state)
    if not draft.foods_raw:
        await callback.answer("Сначала добавьте ингредиенты.", show_alert=True)
        return

    await callback.answer()
    await state.set_state(FoodLogStates.confirm_finish)
    preview = "\n".join(f"• {item}" for item in draft.foods_raw)
    await callback.message.answer(
        "Проверьте список ингредиентов. Готовы перейти к оценке состояния?\n"
        f"{preview}",
        reply_markup=confirm_finish_keyboard(),
    )


@router.callback_query(FoodLogStates.confirm_finish, AddFlowAction.filter(F.action == "back"))
async def cb_back_to_adding(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(FoodLogStates.adding_foods)
    await callback.message.answer(
        "Введите дополнительные ингредиенты или завершите ввод.",
        reply_markup=adding_foods_keyboard(),
    )


@router.callback_query(
    StateFilter(FoodLogStates.adding_foods, FoodLogStates.confirm_finish),
    AddFlowAction.filter(F.action == "cancel"),
)
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(
        "Запись отменена. Нажмите «Добавить еду», чтобы начать заново.",
        reply_markup=start_keyboard(),
    )


@router.callback_query(FoodLogStates.confirm_finish, AddFlowAction.filter(F.action == "confirm"))
async def cb_confirm_finish(callback: CallbackQuery, state: FSMContext) -> None:
    draft = await _get_draft(state)
    if not draft.foods_raw:
        await callback.answer("Добавьте хотя бы один ингредиент.", show_alert=True)
        return

    await callback.answer()
    await state.set_state(FoodLogStates.ask_condition_bloating)
    await state.update_data(condition=ConditionDraft().model_dump())
    await callback.message.answer(
        "Есть ли вздутие?", reply_markup=condition_bool_keyboard("bloating")
    )


@router.callback_query(
    FoodLogStates.ask_condition_bloating,
    ConditionBoolAction.filter(),
)
async def cb_condition_bloating(
    callback: CallbackQuery,
    callback_data: ConditionBoolAction,
    state: FSMContext,
) -> None:
    if callback_data.symptom != "bloating":
        await callback.answer("Сейчас задаю другой вопрос.", show_alert=True)
        return
    if callback_data.value == "cancel":
        await _cancel_condition(callback, state)
        return

    condition = await _get_condition(state)
    condition.bloating = callback_data.value == "yes"
    await state.update_data(condition=condition.model_dump())
    await state.set_state(FoodLogStates.ask_condition_diarrhea)
    await callback.answer()
    await callback.message.answer(
        "Есть ли диарея?", reply_markup=condition_bool_keyboard("diarrhea")
    )


@router.callback_query(
    FoodLogStates.ask_condition_diarrhea,
    ConditionBoolAction.filter(),
)
async def cb_condition_diarrhea(
    callback: CallbackQuery,
    callback_data: ConditionBoolAction,
    state: FSMContext,
) -> None:
    if callback_data.symptom != "diarrhea":
        await callback.answer("Сейчас задаю другой вопрос.", show_alert=True)
        return
    if callback_data.value == "cancel":
        await _cancel_condition(callback, state)
        return

    condition = await _get_condition(state)
    condition.diarrhea = callback_data.value == "yes"
    await state.update_data(condition=condition.model_dump())
    await state.set_state(FoodLogStates.ask_condition_well_being)
    await callback.answer()
    await callback.message.answer(
        "Оцените самочувствие от 1 (плохо) до 10 (отлично).",
        reply_markup=condition_well_being_keyboard(),
    )


@router.callback_query(
    FoodLogStates.ask_condition_well_being,
    ConditionWellBeingAction.filter(),
)
async def cb_condition_well_being(
    callback: CallbackQuery,
    callback_data: ConditionWellBeingAction,
    state: FSMContext,
) -> None:
    condition = await _get_condition(state)
    condition.well_being = callback_data.score
    if not condition.is_complete:
        await callback.answer("Пожалуйста, ответьте на все вопросы.", show_alert=True)
        return

    draft = await _get_draft(state)
    model = Condition(
        bloating=bool(condition.bloating),
        diarrhea=bool(condition.diarrhea),
        well_being=condition.well_being or 1,
    )
    await state.set_state(FoodLogStates.persisting)
    service = _food_event_service()
    result = await service.persist_event(draft, model)
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        "Записал событие. Продукты сохранены в FoodLog и симптомы — в ConditionLog.\n"
        f"Всего ингредиентов: {len(result.foods)}.",
        reply_markup=start_keyboard(),
    )


def _extract_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


async def _get_draft(state: FSMContext) -> FoodEventDraft:
    state_data = await state.get_data()
    draft_data = state_data.get("draft")
    if not draft_data:
        draft_data = FoodEventDraft(started_at=_time_service().now()).model_dump()
        await state.update_data(draft=draft_data)
    return FoodEventDraft.model_validate(draft_data)


async def _get_condition(state: FSMContext) -> ConditionDraft:
    data = await state.get_data()
    condition_data = data.get("condition") or ConditionDraft().model_dump()
    return ConditionDraft.model_validate(condition_data)


async def _cancel_condition(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(
        "Фиксация отменена. Ничего не сохранено. Нажмите «Добавить еду», чтобы начать заново.",
        reply_markup=start_keyboard(),
    )
