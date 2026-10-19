from __future__ import annotations

from typing import Any

from pulsar.ports.decision import DecisionPort, DecisionRequest, Question


CHAT_TOOLS = {
    "overview": "Show accounts, risk, and promotion board",
    "list_factors": "List factors and promotion state",
    "why_not_promoted": "Explain a rejected factor",
    "start_research": "Run an RSI-family research cycle",
    "risk_status": "Show kill switch and books",
    "kill": "Trip the kill switch",
    "paper_trade": "Place a tiny paper order for a promoted factor",
}


class ChatRouter:
    def __init__(self, decision: DecisionPort) -> None:
        self.decision = decision

    def route(self, text: str) -> str:
        resp = self.decision.decide(
            DecisionRequest(
                state={"intent": text, "text": text},
                questions={
                    "chat_tool": Question(
                        type="choice",
                        instructions="Pick the operator tool for this user message.",
                        options=CHAT_TOOLS,
                    )
                },
            )
        )
        return str(resp.answers["chat_tool"].selected)  # type: ignore[union-attr]


def format_overview(payload: dict[str, Any]) -> str:
    kill = payload.get("kill") or {}
    lines = [
        "Pulsar is paper-first. LLM never places live orders.",
        f"Live enabled: {payload.get('live_enabled')}",
        f"Kill switch: {'TRIPPED ' + str(kill.get('reason')) if kill.get('tripped') else 'armed'}",
    ]
    for acct in payload.get("accounts") or []:
        lines.append(
            f"- {acct['market_id']} {acct['mode']} equity={acct['equity']:.2f} cash={acct['cash']:.2f}"
        )
    board = payload.get("board") or []
    paper = [b for b in board if b.get("state") == "paper"]
    rejected = [b for b in board if b.get("state") == "rejected"]
    lines.append(f"Promoted to paper: {len(paper)}; rejected: {len(rejected)}.")
    return "\n".join(lines)
