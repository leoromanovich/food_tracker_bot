from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from ..domain.normalize import sanitize_filename
from .file_store import FileStore


class FoodsService:
    def __init__(self, file_store: FileStore, foods_dir: str = "Foods"):
        self.file_store = file_store
        self.foods_dir = foods_dir

    async def ensure_notes(self, foods: Iterable[str]) -> List[Path]:
        created_paths: List[Path] = []
        for food in foods:
            filename = f"{sanitize_filename(food)}.md"
            path = Path(self.foods_dir) / filename
            result = await self.file_store.ensure_file(path, default_content=f"# {food}\n")
            created_paths.append(result)
        return created_paths
