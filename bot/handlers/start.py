from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from ..ui.callbacks import AddFlowAction
from ..ui.keyboards import start_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я помогу зафиксировать приём пищи. Нажмите “Добавить еду”, чтобы начать.",
        reply_markup=start_keyboard(),
    )


@router.callback_query(AddFlowAction.filter(F.action == "condition"))
async def cb_condition_placeholder(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Отдельная запись самочувствия скоро появится. Пока что ответьте на вопросы "
        "после добавления еды.",
        reply_markup=start_keyboard(),
    )
