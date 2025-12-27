#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
from unittest.mock import DEFAULT

import requests

DEFAULT_MODEL = "openai/gpt-5-nano"
# DEFAULT_MODEL = "openai/gpt-4.1-mini"
# DEFAULT_MODEL = "openai/gpt-5.2"
# DEFAULT_MODEL = "openai/gpt-oss-120b"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Отправляет изображение состава продукта в OpenRouter и выводит распознанный текст."
    )
    parser.add_argument("image", type=Path, help="Путь к изображению (например, img.jpg)")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Имя модели OpenRouter (по умолчанию {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--prompt",
        default=(
            "На изображении текст состава продукта. Верни ингредиенты построчно, "
            "как они перечислены, без нумерации и лишних символов."
        ),
        help="Пользовательский промпт для LLM.",
    )
    return parser


def load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY не установлен в окружении.")
    return key


def encode_image(path: Path) -> str:
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("utf-8")
    suffix = path.suffix.lower()
    mime = "image/jpeg"
    if suffix in {".png"}:
        mime = "image/png"
    elif suffix in {".webp"}:
        mime = "image/webp"
    return f"data:{mime};base64,{encoded}"


def send_request(image_b64: str, prompt: str, model: str, api_key: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты помогаешь извлекать состав продукта с фотографии. "
                    "Верни ингредиенты в виде текста, где каждая строка соответствует одному пункту."
                ),
                },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_b64,
                            # опционально:
                            # "detail": "high",
                            },
                        },
                    ],
                },
            ],
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/leoromanovich/food_calendar",
        "Content-Type": "application/json",
        }

    response = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(payload), timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.image.exists():
        raise FileNotFoundError(f"Файл {args.image} не найден.")

    api_key = load_api_key()
    image_data = encode_image(args.image)
    result = send_request(image_data, args.prompt, args.model, api_key)
    print("Ответ модели:")
    print(result)


if __name__ == "__main__":
    main()
