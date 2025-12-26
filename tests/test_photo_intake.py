import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import photo
from bot.services.photo_intake import PhotoIntakeConfig, PhotoIntakeService


class StubTimeService:
    def now(self):
        return datetime(2025, 3, 12, 19, 30, tzinfo=ZoneInfo("UTC"))


class StubPhoto:
    def __init__(self, file_id: str):
        self.file_id = file_id


class StubFile:
    def __init__(self, file_path: str):
        self.file_path = file_path


class StubDownload:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload


class StubBot:
    def __init__(self, *, raise_on_download: bool = False):
        self.raise_on_download = raise_on_download

    async def get_file(self, file_id: str) -> StubFile:
        return StubFile(file_path=f"/tmp/{file_id}.jpg")

    async def download_file(self, file_path: str) -> StubDownload:
        if self.raise_on_download:
            raise RuntimeError("download failed")
        return StubDownload(b"image-bytes")


class StubMessage:
    def __init__(self, bot: StubBot | None, photos: list[StubPhoto]):
        self.bot = bot
        self.photo = photos
        self.answers: list[str] = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append(text)


class StubPhotoIntakeService(PhotoIntakeService):
    def __init__(self, *, kind: str = "dish", ingredients: list[str] | None = None):
        super().__init__(PhotoIntakeConfig(url="http://localhost", token=None))
        self._kind = kind
        self._ingredients = ingredients if ingredients is not None else []

    async def classify_image(self, image: bytes):
        return self._kind

    async def dish_to_ingredients(self, image: bytes):
        return list(self._ingredients)

    async def ocr_ingredients(self, image: bytes):
        return list(self._ingredients)


def test_parse_kind_defaults_to_dish():
    assert PhotoIntakeService._parse_kind({"kind": "ingredients"}) == "ingredients"
    assert PhotoIntakeService._parse_kind({"kind": "dish"}) == "dish"
    assert PhotoIntakeService._parse_kind({}) == "dish"
    assert PhotoIntakeService._parse_kind({"kind": "unknown"}) == "dish"


def test_parse_ingredients_filters_empty():
    payload = {"ingredients": [" bread ", "", "  ", 123]}
    assert PhotoIntakeService._parse_ingredients(payload) == ["bread", "123"]
    assert PhotoIntakeService._parse_ingredients({"ingredients": "text"}) == []


def test_handle_photo_empty_ingredients():
    asyncio.run(_run_handle_photo_empty_ingredients())


async def _run_handle_photo_empty_ingredients():
    photo.setup_dependencies(
        StubPhotoIntakeService(kind="dish", ingredients=[]), StubTimeService()
    )
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=StorageKey(bot_id=1, chat_id=1, user_id=1))

    message = StubMessage(StubBot(), [StubPhoto("file-1")])
    await photo.handle_photo(message, state)

    assert message.answers == [
        "Не удалось извлечь ингредиенты. Попробуйте другое фото или используйте /add."
    ]
    assert await state.get_state() is None


def test_handle_photo_download_error():
    asyncio.run(_run_handle_photo_download_error())


async def _run_handle_photo_download_error():
    photo.setup_dependencies(
        StubPhotoIntakeService(kind="dish", ingredients=["bread"]),
        StubTimeService(),
    )
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=StorageKey(bot_id=1, chat_id=1, user_id=1))

    message = StubMessage(StubBot(raise_on_download=True), [StubPhoto("file-1")])
    await photo.handle_photo(message, state)

    assert message.answers == [
        "Не смог загрузить фото. Попробуйте отправить ещё раз или используйте /add."
    ]
    assert await state.get_state() is None
