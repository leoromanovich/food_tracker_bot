#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.config import load_settings


def count_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return sum(1 for path in directory.iterdir() if path.is_file())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Анализирует содержимое data/, показывая количество файлов в логах."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="Путь к папке с данными. По умолчанию используется DATA_DIR из конфигурации.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = load_settings()
    data_dir = (args.data_dir or settings.data_dir).resolve()

    foods_dir = data_dir / "Foods"
    condition_dir = data_dir / "ConditionLog"
    foodlog_dir = data_dir / "FoodLog"

    ingredients_count = count_files(foods_dir)
    condition_count = count_files(condition_dir)
    foodlog_count = count_files(foodlog_dir)

    print(f"Папка данных: {data_dir}")
    print(f"Ингредиентов в базе: {ingredients_count}")
    print(f"Записей состояния: {condition_count}")
    print(f"Приёмов пищи: {foodlog_count}")


if __name__ == "__main__":
    main()
