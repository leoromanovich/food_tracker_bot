#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Обучает простую модель, которая предсказывает вздутие по набору ингредиентов."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="Путь к директории с данными (по умолчанию DATA_DIR).",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Доля тестовой выборки для оценки качества (0-1).",
    )
    return parser


def load_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    yaml_text = text[3:end]
    try:
        return yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError:
        return {}


def clean_food_entry(value: str) -> str:
    value = value.strip()
    if value.startswith("[[") and value.endswith("]]"):
        value = value[2:-2]
    return value.strip().lower()


def load_food_events(directory: Path) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    if not directory.exists():
        return result
    for file in directory.glob("*.md"):
        payload = load_frontmatter(file)
        foods: Sequence[str] = payload.get("foods") or []
        cleaned = [clean_food_entry(item) for item in foods if item]
        if cleaned:
            result[file.stem] = cleaned
    return result


def load_conditions(directory: Path) -> Dict[str, bool]:
    result: Dict[str, bool] = {}
    if not directory.exists():
        return result
    for file in directory.glob("*.md"):
        payload = load_frontmatter(file)
        symptoms = payload.get("symptoms") or {}
        bloating = bool(symptoms.get("bloating"))
        result[file.stem] = bloating
    return result


def build_dataset(
    foods: Dict[str, List[str]], conditions: Dict[str, bool]
) -> Tuple[List[List[str]], List[int]]:
    x: List[List[str]] = []
    y: List[int] = []
    for key, ingredient_list in foods.items():
        if key not in conditions:
            continue
        x.append(ingredient_list)
        y.append(1 if conditions[key] else 0)
    return x, y


def train_model(
    x: List[List[str]], y: List[int], test_size: float
) -> None:
    if len(x) < 2 or len(set(y)) < 2:
        print("Недостаточно данных для обучения (требуются разные метки и минимум 2 записи).")
        return

    mlb = MultiLabelBinarizer()
    x_transformed = mlb.fit_transform(x)

    x_train, x_test, y_train, y_test = train_test_split(
        x_transformed,
        y,
        test_size=min(max(test_size, 0.1), 0.9),
        random_state=42,
        stratify=y,
    )

    model = LogisticRegression(max_iter=1000, solver="liblinear")
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Точность на тесте: {accuracy:.3f}")
    print(classification_report(y_test, y_pred, digits=3))

    contributions = sorted(
        zip(mlb.classes_, model.coef_[0]),
        key=lambda pair: abs(pair[1]),
        reverse=True,
    )
    print("Наибольший вклад ингредиентов во вздутие:")
    for ingredient, weight in contributions[:15]:
        print(f"  {ingredient:<30} {weight:+.3f}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = load_settings()
    data_dir = (args.data_dir or settings.data_dir).resolve()

    foods_dir = data_dir / "FoodLog"
    condition_dir = data_dir / "ConditionLog"

    foods = load_food_events(foods_dir)
    conditions = load_conditions(condition_dir)

    x, y = build_dataset(foods, conditions)
    print(f"Найдено {len(x)} событий с состоянием.")
    if not x:
        print("Данных для обучения нет.")
        return

    train_model(x, y, args.test_size)


if __name__ == "__main__":
    main()
