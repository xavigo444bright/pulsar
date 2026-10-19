"""LLM-as-judge DecisionPort. Still returns typed answers; never places orders."""

from __future__ import annotations

import json

import httpx

from pulsar.config import Settings
from pulsar.ports.decision import (
    ChoiceAnswer,
    DecisionRequest,
    DecisionResponse,
    NoulAnswer,
    ScoreAnswer,
    validate_questions,
)


class LLMJudgeDecisionPort:
    backend = "llm"

    def __init__(self, settings: Settings, fallback) -> None:
        self.settings = settings
        self.fallback = fallback

    def decide(self, request: DecisionRequest) -> DecisionResponse:
        validate_questions(request.questions)
        if not self.settings.pulsar_llm_api_key:
            return self.fallback.decide(request)
        schema = {
            name: q.model_dump()
            for name, q in request.questions.items()
        }
        prompt = (
            "Answer each typed question. Return JSON object mapping question "
            "names to {type, and noul | selected+probabilities+confidence | "
            "score+distribution+confidence}. No prose.\n"
            f"STATE:\n{json.dumps(request.state, default=str)[:8000]}\n"
            f"QUESTIONS:\n{json.dumps(schema)}"
        )
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(
                    f"{self.settings.pulsar_llm_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.pulsar_llm_api_key}"},
                    json={
                        "model": self.settings.pulsar_llm_model,
                        "temperature": 0,
                        "messages": [
                            {"role": "system", "content": "You are a typed decision model."},
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(_extract_json(content))
            answers = {}
            for name, question in request.questions.items():
                raw = data.get(name) or {}
                if question.type == "noul":
                    answers[name] = NoulAnswer(noul=float(raw.get("noul", 0.5)))
                elif question.type == "score":
                    answers[name] = ScoreAnswer(
                        score=float(raw.get("score", 1)),
                        distribution=dict(raw.get("distribution") or {}),
                        confidence=float(raw.get("confidence", 0.5)),
                    )
                else:
                    probs = dict(raw.get("probabilities") or {})
                    answers[name] = ChoiceAnswer(
                        selected=str(raw.get("selected") or next(iter(question.options or {}), "")),
                        probabilities=probs,
                        confidence=float(raw.get("confidence", 0.5)),
                    )
            return DecisionResponse(backend="llm", answers=answers)
        except Exception:  # noqa: BLE001
            return self.fallback.decide(request)


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text
