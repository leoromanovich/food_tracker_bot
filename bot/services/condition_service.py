from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from ..domain.models import Condition
from .file_store import FileStore


@dataclass(slots=True)
class ConditionRecord:
    path: Path
    content: str


class ConditionService:
    def __init__(self, file_store: FileStore, log_dir: str = "ConditionLog"):
        self.file_store = file_store
        self.log_dir = log_dir

    async def persist(
        self, timestamp: datetime, short_id: str, condition: Condition
    ) -> ConditionRecord:
        filename = self._build_filename(timestamp, short_id)
        content = self._render_markdown(timestamp, condition)
        path = await self.file_store.write_text(Path(self.log_dir) / filename, content)
        return ConditionRecord(path=path, content=content)

    def _build_filename(self, timestamp: datetime, short_id: str) -> str:
        slug = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        return f"{slug}_{short_id}.md"

    def _render_markdown(self, timestamp: datetime, condition: Condition) -> str:
        payload = {
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M"),
            "symptoms": {
                "bloating": bool(condition.bloating),
                "diarrhea": bool(condition.diarrhea),
                "well_being": condition.well_being,
            },
        }
        yaml_body = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False).strip()
        return f"---\n{yaml_body}\n---\n"
