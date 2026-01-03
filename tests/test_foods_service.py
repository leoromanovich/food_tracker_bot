import asyncio
from pathlib import Path

from bot.services.file_store import FileStore
from bot.services.foods_service import FoodsService


def test_foods_service_creates_unique_files_for_collisions(tmp_path: Path):
    asyncio.run(_run_collision_test(tmp_path))


async def _run_collision_test(tmp_path: Path):
    file_store = FileStore(tmp_path)
    service = FoodsService(file_store)

    results = await service.ensure_notes(["сыр", "сыр!"])

    filenames = [path.name for path in results]
    assert len(filenames) == 2
    assert len(set(filenames)) == 2

    contents = [Path(path).read_text(encoding="utf-8") for path in results]
    assert 'original_name: "сыр"' in contents[0] + contents[1]
    assert 'original_name: "сыр!"' in contents[0] + contents[1]
    for content in contents:
        assert "#foodtracker" in content
