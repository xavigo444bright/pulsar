from __future__ import annotations

from pulsar.research.rsi.miner import candidate_universe, describe_for_llm


class Researcher:
    """Proposes RSI-family hypotheses. Has no order tool."""

    name = "researcher"
    tools = ("list_family", "propose")

    def propose(self) -> list[dict]:
        return [
            {
                "id": spec.id,
                "name": spec.name,
                "description": spec.description,
                "params": spec.params,
                "kind": spec.kind,
                "complexity": spec.complexity,
            }
            for spec in candidate_universe()
        ]

    def prompt_block(self) -> str:
        return describe_for_llm(candidate_universe())
