"""Optional TypeSafe Jev backend. Falls back to rules if the key is missing."""

from __future__ import annotations

from typing import Any

import httpx

from pulsar.ports.decision import (
    ChoiceAnswer,
    DecisionRequest,
    DecisionResponse,
    NoulAnswer,
    Question,
    ScoreAnswer,
    validate_questions,
)


class JevDecisionPort:
    backend = "jev"

    def __init__(self, api_key: str, base_url: str, fallback) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.fallback = fallback

    def decide(self, request: DecisionRequest) -> DecisionResponse:
        validate_questions(request.questions)
        if not self.api_key:
            return self.fallback.decide(request)
        payload = {
            "model": "jev-latest",
            "state": request.state,
            "questions": {name: _to_jev(q) for name, q in request.questions.items()},
        }
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(
                    f"{self.base_url}/systemone",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
            answers = {
                name: _from_jev(request.questions[name], raw)
                for name, raw in (data.get("answers") or data).items()
                if name in request.questions
            }
            if len(answers) != len(request.questions):
                return self.fallback.decide(request)
            return DecisionResponse(backend="jev", answers=answers)
        except Exception:  # noqa: BLE001 — Jev is optional; rules keep the loop alive
            return self.fallback.decide(request)


def _to_jev(question: Question) -> dict[str, Any]:
    body: dict[str, Any] = {"type": question.type, "instructions": question.instructions}
    if question.type == "choice":
        body["options"] = question.options or {}
    if question.type == "score":
        body["criteria"] = question.levels or []
    return body


def _from_jev(question: Question, raw: dict[str, Any]):
    if question.type == "noul":
        return NoulAnswer(noul=float(raw.get("noul", 0.5)))
    if question.type == "score":
        return ScoreAnswer(
            score=float(raw.get("score", 1.0)),
            distribution=dict(raw.get("distribution") or {}),
            confidence=float(raw.get("confidence", 0.5)),
        )
    probs = dict(raw.get("probabilities") or {})
    selected = str(raw.get("selected") or next(iter(probs), ""))
    return ChoiceAnswer(
        selected=selected,
        probabilities=probs,
        confidence=float(raw.get("confidence", 0.5)),
    )
