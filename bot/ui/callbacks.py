from __future__ import annotations

from typing import Literal

from aiogram.filters.callback_data import CallbackData


class AddFlowAction(CallbackData, prefix="addflow"):
    action: Literal[
        "start", "continue", "finish", "cancel", "confirm", "back", "condition"
    ]


class ConditionBoolAction(CallbackData, prefix="condbool"):
    symptom: Literal["bloating", "diarrhea"]
    value: Literal["yes", "no", "cancel"]


class ConditionWellBeingAction(CallbackData, prefix="condwb"):
    score: int
