from __future__ import annotations

from pulsar.research.rsi.family import SEEDS, FactorSpec


def candidate_universe() -> list[FactorSpec]:
    """RSI-family search space for v1. LLM may only pick/compose inside this list."""
    extra = [
        FactorSpec(
            id="rsi21_mr",
            name="RSI(21) mean reversion",
            family="rsi",
            kind="rsi_mean_reversion",
            params={"period": 21, "oversold": 30, "overbought": 70},
            description="Slower RSI mean reversion.",
            complexity=1,
        ),
        FactorSpec(
            id="rsi2_mr",
            name="RSI(2) mean reversion",
            family="rsi",
            kind="rsi_mean_reversion",
            params={"period": 2, "oversold": 10, "overbought": 90},
            description="Connors-style RSI(2).",
            complexity=1,
        ),
        FactorSpec(
            id="noise_control",
            name="Random noise control",
            family="rsi",
            kind="noise",
            params={"seed": 99},
            description="Negative control. Must never promote.",
            complexity=9,
        ),
    ]
    return [*SEEDS, *extra]


def describe_for_llm(specs: list[FactorSpec]) -> str:
    lines = [
        "Only propose factors from this RSI family. Do not invent unrelated operators.",
        "A new factor must beat RSI(14) mean reversion on the same cost model.",
    ]
    for spec in specs:
        lines.append(f"- {spec.id}: {spec.name} :: {spec.description} params={spec.params}")
    return "\n".join(lines)
