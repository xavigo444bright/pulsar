from __future__ import annotations

from dataclasses import dataclass, field

from pulsar.backtest.engine import BacktestResult, run_signal, walk_forward
from pulsar.markets.synthetic import bars_to_arrays
from pulsar.ports.market import Bar
from pulsar.research.rsi.family import BASELINE_ID, FactorSpec, is_rsi_family, signal_from_spec


@dataclass
class GateReport:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


def evaluate_factor(
    spec: FactorSpec,
    bars: list[Bar],
    fee_bps: float,
    baseline_spec: FactorSpec,
) -> GateReport:
    arrays = bars_to_arrays(bars)
    close = arrays["close"]
    reasons: list[str] = []
    if len(close) < 200:
        return GateReport(False, ["insufficient_bars"], {"bars": len(close)})
    if not is_rsi_family(spec) and spec.kind != "noise":
        reasons.append("not_rsi_family")

    signal = signal_from_spec(spec)(arrays)
    base_signal = signal_from_spec(baseline_spec)(arrays)
    result = run_signal(close, signal, fee_bps)
    baseline = run_signal(close, base_signal, fee_bps)
    folds = walk_forward(close, signal, fee_bps, folds=3)
    base_folds = walk_forward(close, base_signal, fee_bps, folds=3)
    fold_wins = 0
    for cand, base in zip(folds, base_folds, strict=False):
        if cand.sharpe > base.sharpe:
            fold_wins += 1
    test_len = max(80, len(close) // 5)
    test = run_signal(close[-test_len:], signal[-test_len:], fee_bps)
    base_test = run_signal(close[-test_len:], base_signal[-test_len:], fee_bps)

    excess = result.sharpe - baseline.sharpe
    metrics = {
        "sharpe": result.sharpe,
        "baseline_sharpe": baseline.sharpe,
        "excess_sharpe": excess,
        "turnover": result.turnover,
        "max_drawdown": result.max_drawdown,
        "trades": result.trades,
        "fold_wins": fold_wins,
        "folds": len(folds),
        "test_sharpe": test.sharpe,
        "baseline_test_sharpe": base_test.sharpe,
        "complexity": spec.complexity,
        "factor_id": spec.id,
        "is_baseline": spec.id == BASELINE_ID,
    }

    if spec.id == BASELINE_ID:
        return GateReport(True, ["baseline_reference"], metrics)

    if spec.kind == "noise" or reasons:
        reasons.append("rejected_family_or_noise")
        return GateReport(False, reasons, metrics)
    if excess <= 0:
        reasons.append("did_not_beat_rsi14_baseline")
    if test.sharpe <= base_test.sharpe:
        reasons.append("holdout_did_not_beat_baseline")
    if fold_wins < max(1, len(folds) // 2 + (1 if len(folds) else 0) - 1):
        # majority of folds must beat baseline
        if fold_wins * 2 < len(folds):
            reasons.append("walk_forward_majority_failed")
    if result.turnover > 0.6:
        reasons.append("turnover_too_high")
    if result.max_drawdown > 0.45:
        reasons.append("drawdown_too_high")
    if spec.complexity > 6:
        reasons.append("too_complex")
    return GateReport(passed=len(reasons) == 0, reasons=reasons, metrics=metrics)


def fragility(
    primary: GateReport, secondary: GateReport, disaster_sharpe: float = -0.5
) -> GateReport:
    """Same factor must not be a disaster on the second market."""
    if not primary.passed:
        return primary
    sec_sharpe = float(secondary.metrics.get("sharpe", 0.0))
    if sec_sharpe < disaster_sharpe:
        return GateReport(
            False,
            primary.reasons + ["fragile_cross_market"],
            {**primary.metrics, "secondary_sharpe": sec_sharpe},
        )
    merged = {**primary.metrics, "secondary_sharpe": sec_sharpe, "fragile": False}
    return GateReport(True, [], merged)
