from __future__ import annotations

from pulsar.config import Settings
from pulsar.decision.jev import JevDecisionPort
from pulsar.decision.llm_judge import LLMJudgeDecisionPort
from pulsar.decision.rules import RuleDecisionPort
from pulsar.ports.decision import DecisionPort


def get_decision_port(settings: Settings) -> DecisionPort:
    rules = RuleDecisionPort()
    backend = settings.pulsar_decision_backend.lower().strip()
    if backend == "jev":
        return JevDecisionPort(
            api_key=settings.typesafe_api_key,
            base_url=settings.typesafe_base_url,
            fallback=rules,
        )
    if backend == "llm":
        return LLMJudgeDecisionPort(settings=settings, fallback=rules)
    return rules
