from __future__ import annotations

from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(lambda message: bool(message.photo))
async def handle_photo(message: Message) -> None:
    await message.answer(
        "Обработка фотографий пока в разработке. "
        "Пожалуйста, используйте /add и перечислите ингредиенты текстом."
    )
