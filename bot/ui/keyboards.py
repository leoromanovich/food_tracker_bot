from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import AddFlowAction, ConditionBoolAction, ConditionWellBeingAction


def start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить еду", callback_data=AddFlowAction(action="start"))
    builder.button(text="Отправить фото (скоро)", callback_data=AddFlowAction(action="back"))
    builder.button(text="Самочувствие", callback_data=AddFlowAction(action="condition"))
    builder.adjust(1)
    return builder.as_markup()


def adding_foods_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Продолжить ввод", callback_data=AddFlowAction(action="continue"))
    builder.button(text="Завершить", callback_data=AddFlowAction(action="finish"))
    builder.button(text="Отменить", callback_data=AddFlowAction(action="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def confirm_finish_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Сохранить и продолжить", callback_data=AddFlowAction(action="confirm"))
    builder.button(text="Вернуться к вводу", callback_data=AddFlowAction(action="back"))
    builder.button(text="Отменить", callback_data=AddFlowAction(action="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def condition_bool_keyboard(symptom: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Да",
        callback_data=ConditionBoolAction(symptom=symptom, value="yes"),
    )
    builder.button(
        text="Нет",
        callback_data=ConditionBoolAction(symptom=symptom, value="no"),
    )
    builder.button(
        text="Отменить",
        callback_data=ConditionBoolAction(symptom=symptom, value="cancel"),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def condition_well_being_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for score in range(1, 11):
        builder.button(
            text=str(score),
            callback_data=ConditionWellBeingAction(score=score),
        )
    builder.adjust(5)
    return builder.as_markup()
