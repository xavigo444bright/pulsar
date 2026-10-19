from __future__ import annotations

from dataclasses import dataclass

from pulsar.backtest.gates import GateReport, evaluate_factor, fragility
from pulsar.db import Database
from pulsar.ports.decision import DecisionRequest, Question
from pulsar.ports.decision import DecisionPort
from pulsar.ports.market import MarketPort
from pulsar.research.rsi.family import BASELINE_ID, FactorSpec, SEEDS
from pulsar.research.rsi.miner import candidate_universe

STATES = ("hypothesis", "candidate", "paper", "live", "retired", "rejected")


@dataclass
class PromotionRecord:
    factor: FactorSpec
    state: str
    reason: str
    reports: dict[str, GateReport]


class PromotionMachine:
    def __init__(self, db: Database, decision: DecisionPort) -> None:
        self.db = db
        self.decision = decision

    def run_cycle(
        self,
        primary: MarketPort,
        secondary: MarketPort,
        primary_symbol: str,
        secondary_symbol: str,
        fee_bps_primary: float,
        fee_bps_secondary: float,
        live_enabled: bool = False,
    ) -> list[PromotionRecord]:
        baseline = next(s for s in SEEDS if s.id == BASELINE_ID)
        primary_bars = primary.candles(primary_symbol, limit=800)
        secondary_bars = secondary.candles(secondary_symbol, limit=800)
        records: list[PromotionRecord] = []
        for spec in candidate_universe():
            rec = self._promote_one(
                spec,
                baseline,
                primary,
                secondary,
                primary_bars,
                secondary_bars,
                primary_symbol,
                secondary_symbol,
                fee_bps_primary,
                fee_bps_secondary,
                live_enabled,
            )
            records.append(rec)
        return records

    def _promote_one(
        self,
        spec: FactorSpec,
        baseline: FactorSpec,
        primary: MarketPort,
        secondary: MarketPort,
        primary_bars,
        secondary_bars,
        primary_symbol: str,
        secondary_symbol: str,
        fee_p: float,
        fee_s: float,
        live_enabled: bool,
    ) -> PromotionRecord:
        self.db.upsert_factor(spec.id, spec.name, spec.family, spec.params | {"kind": spec.kind})
        self.db.add_hypothesis(f"h-{spec.id}", spec.id, spec.name, spec.description, "open")
        decision = self.decision.decide(
            DecisionRequest(
                state={
                    "name": spec.name,
                    "description": spec.description,
                    "family": spec.family,
                    "spec": {"kind": spec.kind, "family": spec.family},
                    "complexity": spec.complexity,
                    "novelty": min(1.0, spec.complexity / 5),
                },
                questions={
                    "is_rsi_family": Question(
                        type="noul",
                        instructions="The hypothesis belongs to the RSI / StochRSI / RSI-divergence family.",
                    ),
                    "novelty": Question(
                        type="score",
                        instructions="Novelty versus the RSI(14) seed.",
                        levels=["duplicate", "near", "fresh", "very_new"],
                    ),
                    "disposition": Question(
                        type="choice",
                        instructions="What should happen next?",
                        options={
                            "gauntlet": "Run statistical gates",
                            "memory": "Store as a failed idea",
                            "discard": "Drop immediately",
                        },
                    ),
                },
            )
        )
        self.db.log_decision(
            decision.backend,
            {"factor": spec.id},
            {k: v.model_dump() for k, v in decision.answers.items()},
        )
        rsi_p = float(decision.answers["is_rsi_family"].noul)  # type: ignore[union-attr]
        if spec.kind != "noise" and rsi_p < 0.5:
            reason = "rejected_by_decisionport_not_rsi_family"
            self.db.set_promotion(spec.id, "rejected", reason)
            self.db.remember_failure(spec.name, reason, spec.id)
            return PromotionRecord(spec, "rejected", reason, {})

        primary_rep = evaluate_factor(spec, primary_bars, fee_p, baseline)
        secondary_rep = evaluate_factor(spec, secondary_bars, fee_s, baseline)
        self.db.add_evaluation(spec.id, primary.market_id, primary_symbol, primary_rep.metrics, primary_rep.passed)
        self.db.add_evaluation(
            spec.id, secondary.market_id, secondary_symbol, secondary_rep.metrics, secondary_rep.passed
        )
        combined = fragility(primary_rep, secondary_rep)
        disp = self.decision.decide(
            DecisionRequest(
                state={
                    "name": spec.name,
                    "description": spec.description,
                    "family": spec.family,
                    "spec": {"kind": spec.kind},
                    "gates_ran": True,
                    "gates_passed": combined.passed,
                    "excess_sharpe": combined.metrics.get("excess_sharpe", 0.0),
                    "complexity": spec.complexity,
                    "folds_failed": 0 if combined.passed else 2,
                },
                questions={
                    "disposition": Question(
                        type="choice",
                        instructions="Promote to paper, remember failure, or discard.",
                        options={
                            "promote_paper": "Paper trading",
                            "memory": "Write failure memory",
                            "discard": "Discard",
                        },
                    )
                },
            )
        )
        self.db.log_decision(disp.backend, {"factor": spec.id, "stage": "post_gate"}, {k: v.model_dump() for k, v in disp.answers.items()})

        if not combined.passed:
            reason = ",".join(combined.reasons) or "gates_failed"
            self.db.set_promotion(spec.id, "rejected", reason)
            self.db.remember_failure(spec.name, reason, spec.id)
            return PromotionRecord(spec, "rejected", reason, {"primary": primary_rep, "secondary": secondary_rep})

        # Baseline is reference-only; never auto-live.
        if spec.id == BASELINE_ID:
            self.db.set_promotion(spec.id, "candidate", "baseline_reference")
            return PromotionRecord(spec, "candidate", "baseline_reference", {"primary": primary_rep})

        reason = "passed_gates_and_cross_market"
        self.db.set_promotion(spec.id, "paper", reason)
        if live_enabled:
            # Live still requires opt-in plus paper seasoning; v1 records eligibility only.
            self.db.set_promotion(spec.id, "paper", reason + ";live_opt_in_requires_operator")
        return PromotionRecord(
            spec, "paper", reason, {"primary": primary_rep, "secondary": secondary_rep}
        )
