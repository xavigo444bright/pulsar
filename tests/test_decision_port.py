from pulsar.decision.rules import RuleDecisionPort
from pulsar.ports.decision import DecisionRequest, Question


def test_choice_score_noul_shape():
    port = RuleDecisionPort()
    resp = port.decide(
        DecisionRequest(
            state={"name": "RSI(14) mean reversion", "family": "rsi", "spec": {"kind": "rsi_mean_reversion"}},
            questions={
                "is_rsi_family": Question(type="noul", instructions="RSI family?"),
                "novelty": Question(
                    type="score",
                    instructions="Novelty",
                    levels=["duplicate", "near", "fresh", "very_new"],
                ),
                "disposition": Question(
                    type="choice",
                    instructions="Next",
                    options={"gauntlet": "a", "memory": "b", "discard": "c"},
                ),
            },
        )
    )
    noul = resp.answers["is_rsi_family"]
    score = resp.answers["novelty"]
    choice = resp.answers["disposition"]
    assert noul.type == "noul" and noul.noul >= 0.9
    assert score.type == "score" and 1 <= score.score <= 4
    assert choice.type == "choice" and choice.selected in choice.probabilities
    assert abs(sum(choice.probabilities.values()) - 1) < 1e-6


def test_chat_routes_chinese_research():
    port = RuleDecisionPort()
    resp = port.decide(
        DecisionRequest(
            state={"intent": "开始研究", "text": "开始研究"},
            questions={
                "chat_tool": Question(
                    type="choice",
                    instructions="Pick the operator tool",
                    options={
                        "overview": "o",
                        "list_factors": "l",
                        "why_not_promoted": "w",
                        "start_research": "s",
                        "risk_status": "r",
                        "kill": "k",
                        "paper_trade": "p",
                    },
                )
            },
        )
    )
    assert resp.answers["chat_tool"].selected == "start_research"  # type: ignore[union-attr]


def test_noise_is_not_rsi_family():
    port = RuleDecisionPort()
    resp = port.decide(
        DecisionRequest(
            state={"name": "coin flip", "description": "random", "family": "other", "spec": {"kind": "noise"}},
            questions={"is_rsi_family": Question(type="noul", instructions="RSI family membership")},
        )
    )
    assert resp.answers["is_rsi_family"].noul < 0.5  # type: ignore[union-attr]
