"""Jev-shaped DecisionPort.

Input is shared state plus typed questions. Output is probabilities the rest
of the system can consume without parsing prose. Code still owns promotion
thresholds and order placement.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

QuestionType = Literal["choice", "score", "noul"]


class Question(BaseModel):
    type: QuestionType
    instructions: str
    options: dict[str, str] | None = None
    levels: list[str] | None = None


class ChoiceAnswer(BaseModel):
    type: Literal["choice"] = "choice"
    selected: str
    probabilities: dict[str, float]
    confidence: float = Field(ge=0.0, le=1.0)


class ScoreAnswer(BaseModel):
    type: Literal["score"] = "score"
    score: float
    distribution: dict[str, float]
    confidence: float = Field(ge=0.0, le=1.0)


class NoulAnswer(BaseModel):
    type: Literal["noul"] = "noul"
    noul: float = Field(ge=0.0, le=1.0)


Answer = ChoiceAnswer | ScoreAnswer | NoulAnswer


class DecisionRequest(BaseModel):
    state: Any
    questions: dict[str, Question]


class DecisionResponse(BaseModel):
    backend: str
    answers: dict[str, Answer]


@runtime_checkable
class DecisionPort(Protocol):
    backend: str

    def decide(self, request: DecisionRequest) -> DecisionResponse: ...


def merge_answers(*parts: dict[str, Answer]) -> dict[str, Answer]:
    out: dict[str, Answer] = {}
    for part in parts:
        out.update(part)
    return out


def validate_questions(questions: dict[str, Question]) -> None:
    for name, q in questions.items():
        if q.type == "choice" and (not q.options or len(q.options) < 2):
            raise ValueError(f"{name}: choice needs at least two options")
        if q.type == "score":
            levels = q.levels or []
            if not 2 <= len(levels) <= 10:
                raise ValueError(f"{name}: score needs 2-10 ordered levels")
