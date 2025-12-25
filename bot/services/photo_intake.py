from __future__ import annotations

from typing import Literal


class PhotoIntakeService:
    async def classify_image(self, _: bytes) -> Literal["dish", "ingredients"]:
        return "dish"

    async def dish_to_ingredients(self, _: bytes) -> list[str]:
        return []

    async def ocr_ingredients(self, _: bytes) -> list[str]:
        return []
