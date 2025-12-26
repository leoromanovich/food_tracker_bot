from __future__ import annotations

import asyncio
from typing import Sequence

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import Settings, load_settings
from .handlers import add_food, common, photo, start
from .logging_setup import setup_logging
from .services.condition_service import ConditionService
from .services.file_store import FileStore
from .services.food_event_service import FoodEventService
from .services.foods_service import FoodsService
from .services.photo_intake import (
    PhotoIntakeConfig,
    PhotoIntakeService,
    PhotoIntakeStubService,
)
from .services.time_service import TimeService


def build_dispatcher(settings: Settings) -> Dispatcher:
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)

    file_store = FileStore(settings.data_dir)
    time_service = TimeService(settings.timezone)
    foods_service = FoodsService(file_store)
    condition_service = ConditionService(file_store)
    if settings.photo_intake_url:
        photo_config = PhotoIntakeConfig(
            url=settings.photo_intake_url,
            token=settings.photo_intake_token,
        )
        photo_intake_service = PhotoIntakeService(photo_config)
    else:
        photo_intake_service = PhotoIntakeStubService()
    food_event_service = FoodEventService(
        file_store=file_store,
        foods_service=foods_service,
        condition_service=condition_service,
        time_service=time_service,
    )
    add_food.setup_dependencies(food_event_service, time_service)
    photo.setup_dependencies(photo_intake_service, time_service)

    routers: Sequence = (
        start.router,
        add_food.router,
        photo.router,
        common.router,
    )
    for router in routers:
        dispatcher.include_router(router)

    return dispatcher


async def run() -> None:
    setup_logging()
    settings = load_settings()
    dispatcher = build_dispatcher(settings)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run())
