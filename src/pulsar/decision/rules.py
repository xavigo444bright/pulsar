"""Deterministic DecisionPort. No network. Default so clone-and-run works."""

from __future__ import annotations

import math
from typing import Any

from pulsar.ports.decision import (
    ChoiceAnswer,
    DecisionRequest,
    DecisionResponse,
    NoulAnswer,
    Question,
    ScoreAnswer,
    validate_questions,
)

RSI_FAMILY_TOKENS = (
    "rsi",
    "stochrsi",
    "relative strength",
    "oversold",
    "overbought",
    "divergence",
    "wilder",
)


class RuleDecisionPort:
    backend = "rules"

    def decide(self, request: DecisionRequest) -> DecisionResponse:
        validate_questions(request.questions)
        state = request.state if isinstance(request.state, dict) else {"text": str(request.state)}
        answers = {
            name: self._answer(name, question, state)
            for name, question in request.questions.items()
        }
        return DecisionResponse(backend=self.backend, answers=answers)

    def _answer(self, name: str, question: Question, state: dict[str, Any]):
        if question.type == "noul":
            return NoulAnswer(noul=self._noul(name, question, state))
        if question.type == "score":
            return self._score(name, question, state)
        return self._choice(name, question, state)

    def _noul(self, name: str, question: Question, state: dict[str, Any]) -> float:
        blob = _blob(state)
        if name in {"is_rsi_family", "rsi_family"}:
            return 0.97 if _looks_rsi(blob) else 0.08
        if name in {"overfit_suspect", "looks_overfit"}:
            complexity = float(state.get("complexity", 0))
            folds_failed = int(state.get("folds_failed", 0))
            return _clamp(0.15 + 0.12 * complexity + 0.2 * folds_failed)
        if name in {"should_trip_kill", "kill"}:
            if state.get("kill_already"):
                return 1.0
            dd = float(state.get("drawdown_pct", 0.0))
            daily = float(state.get("daily_loss_pct", 0.0))
            max_dd = float(state.get("max_drawdown_pct", 0.08))
            max_daily = float(state.get("max_daily_loss_pct", 0.02))
            if dd >= max_dd or daily >= max_daily:
                return 0.99
            return 0.05
        if name in {"allow_live_order", "live_ok"}:
            if not state.get("live_enabled"):
                return 0.0
            if not state.get("promoted"):
                return 0.0
            if state.get("kill_already"):
                return 0.0
            return 0.2
        if _looks_rsi(blob):
            return 0.85
        return 0.5

    def _score(self, name: str, question: Question, state: dict[str, Any]) -> ScoreAnswer:
        levels = question.levels or ["low", "medium", "high"]
        n = len(levels)
        if name in {"novelty", "novelty_vs_seeds"}:
            raw = float(state.get("novelty", state.get("ast_distance", 0.4)))
        elif name in {"promotion_confidence"}:
            raw = float(state.get("excess_sharpe", 0.0))
            raw = 1 / (1 + math.exp(-raw))  # squash
        else:
            raw = float(state.get("score", 0.5))
        raw = _clamp(raw)
        idx = min(n - 1, int(raw * n)) if raw < 1 else n - 1
        dist = {level: (0.7 if i == idx else 0.3 / max(n - 1, 1)) for i, level in enumerate(levels)}
        total = sum(dist.values())
        dist = {k: v / total for k, v in dist.items()}
        score = sum((i + 1) * dist[level] for i, level in enumerate(levels))
        peak = dist[levels[idx]]
        return ScoreAnswer(score=score, distribution=dist, confidence=_clamp(peak))

    def _choice(self, name: str, question: Question, state: dict[str, Any]) -> ChoiceAnswer:
        options = question.options or {}
        keys = list(options)
        blob = _blob(state) + " " + question.instructions.lower()
        picked = keys[0]
        if name in {"disposition", "next_step"}:
            if not _looks_rsi(blob):
                picked = _prefer(keys, ("discard", "memory", "drop"))
            elif state.get("gates_passed"):
                picked = _prefer(keys, ("promote_paper", "gauntlet", "paper"))
            elif state.get("gates_ran"):
                picked = _prefer(keys, ("memory", "discard"))
            else:
                picked = _prefer(keys, ("gauntlet", "validate", "backtest"))
        elif name in {"tool", "chat_tool"}:
            intent = str(state.get("intent", blob)).lower()
            if any(w in intent for w in ("kill", "停机", "halt")):
                picked = _prefer(keys, ("kill", "risk_status"))
            elif any(w in intent for w in ("why", "为什么", "没晋升", "promote")):
                picked = _prefer(keys, ("why_not_promoted", "list_factors"))
            elif any(w in intent for w in ("research", "挖", "mine", "factor", "研究", "gauntlet")):
                picked = _prefer(keys, ("start_research", "list_factors"))
            elif any(w in intent for w in ("risk", "风控", "回撤")):
                picked = _prefer(keys, ("risk_status",))
            else:
                picked = _prefer(keys, ("overview", "list_factors"))
        weights = {k: (0.72 if k == picked else 0.28 / max(len(keys) - 1, 1)) for k in keys}
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}
        return ChoiceAnswer(
            selected=picked,
            probabilities=weights,
            confidence=weights[picked],
        )


def _blob(state: dict[str, Any]) -> str:
    parts = [str(state.get("name", "")), str(state.get("description", ""))]
    spec = state.get("spec") or {}
    if isinstance(spec, dict):
        parts.append(str(spec.get("kind", "")))
        parts.append(str(spec.get("family", "")))
    parts.append(str(state.get("family", "")))
    parts.append(str(state.get("text", "")))
    return " ".join(parts).lower()


def _looks_rsi(blob: str) -> bool:
    return any(tok in blob for tok in RSI_FAMILY_TOKENS)


def _prefer(keys: list[str], wanted: tuple[str, ...]) -> str:
    for item in wanted:
        for key in keys:
            if item == key or item in key:
                return key
    return keys[0]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
