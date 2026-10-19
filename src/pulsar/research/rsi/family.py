from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

import numpy as np

from pulsar.research.rsi.indicators import rsi, rsi_slope, stoch_rsi

SignalFn = Callable[[dict[str, np.ndarray]], np.ndarray]


@dataclass(frozen=True)
class FactorSpec:
    id: str
    name: str
    family: Literal["rsi"]
    kind: str
    params: dict
    description: str
    complexity: int


def signal_from_spec(spec: FactorSpec) -> SignalFn:
    kind = spec.kind
    p = spec.params

    def _rsi_mr(arrays: dict[str, np.ndarray]) -> np.ndarray:
        values = rsi(arrays["close"], int(p.get("period", 14)))
        sig = np.zeros_like(values)
        sig[values < float(p.get("oversold", 30))] = 1.0
        sig[values > float(p.get("overbought", 70))] = -1.0
        return _hold(sig)

    def _rsi_slope_mr(arrays: dict[str, np.ndarray]) -> np.ndarray:
        values = rsi(arrays["close"], int(p.get("period", 14)))
        slope = rsi_slope(arrays["close"], int(p.get("period", 14)), int(p.get("lookback", 5)))
        sig = np.zeros_like(values)
        sig[(values < float(p.get("oversold", 35))) & (slope > 0)] = 1.0
        sig[(values > float(p.get("overbought", 65))) & (slope < 0)] = -1.0
        return _hold(sig)

    def _stoch_rsi_mr(arrays: dict[str, np.ndarray]) -> np.ndarray:
        values = stoch_rsi(arrays["close"], int(p.get("period", 14)))
        sig = np.zeros_like(values)
        sig[values < float(p.get("oversold", 20))] = 1.0
        sig[values > float(p.get("overbought", 80))] = -1.0
        return _hold(sig)

    def _rsi_div(arrays: dict[str, np.ndarray]) -> np.ndarray:
        close = arrays["close"]
        values = rsi(close, int(p.get("period", 14)))
        look = int(p.get("lookback", 20))
        sig = np.zeros_like(close)
        for i in range(look, len(close)):
            price_ll = close[i] <= close[i - look : i].min()
            rsi_hl = values[i] > values[i - look : i].min()
            price_hh = close[i] >= close[i - look : i].max()
            rsi_lh = values[i] < values[i - look : i].max()
            if price_ll and rsi_hl:
                sig[i] = 1.0
            elif price_hh and rsi_lh:
                sig[i] = -1.0
        return _hold(sig)

    def _rsi_volume(arrays: dict[str, np.ndarray]) -> np.ndarray:
        values = rsi(arrays["close"], int(p.get("period", 14)))
        vol = arrays["volume"]
        vol_ma = np.convolve(vol, np.ones(20) / 20, mode="same")
        boost = vol > vol_ma
        sig = np.zeros_like(values)
        sig[(values < float(p.get("oversold", 30))) & boost] = 1.0
        sig[(values > float(p.get("overbought", 70))) & boost] = -1.0
        return _hold(sig)

    def _noise(arrays: dict[str, np.ndarray]) -> np.ndarray:
        rng = np.random.default_rng(int(p.get("seed", 99)))
        return rng.choice([-1.0, 0.0, 1.0], size=len(arrays["close"]))

    table = {
        "rsi_mean_reversion": _rsi_mr,
        "rsi_slope": _rsi_slope_mr,
        "stoch_rsi": _stoch_rsi_mr,
        "rsi_divergence": _rsi_div,
        "rsi_volume": _rsi_volume,
        "noise": _noise,
    }
    if kind not in table:
        raise ValueError(f"unknown factor kind {kind}")
    return table[kind]


def _hold(raw: np.ndarray) -> np.ndarray:
    """Keep the last non-zero signal until the opposite fire."""
    out = np.zeros_like(raw)
    last = 0.0
    for i, v in enumerate(raw):
        if v != 0:
            last = v
        out[i] = last
    return out


SEEDS: list[FactorSpec] = [
    FactorSpec(
        id="rsi14_mr",
        name="RSI(14) mean reversion",
        family="rsi",
        kind="rsi_mean_reversion",
        params={"period": 14, "oversold": 30, "overbought": 70},
        description="Baseline: buy RSI<30, sell RSI>70, hold through.",
        complexity=1,
    ),
    FactorSpec(
        id="rsi7_mr",
        name="RSI(7) mean reversion",
        family="rsi",
        kind="rsi_mean_reversion",
        params={"period": 7, "oversold": 25, "overbought": 75},
        description="Faster RSI mean reversion inside the family.",
        complexity=1,
    ),
    FactorSpec(
        id="rsi14_slope",
        name="RSI(14) with slope filter",
        family="rsi",
        kind="rsi_slope",
        params={"period": 14, "lookback": 5, "oversold": 35, "overbought": 65},
        description="Require RSI turning before entry.",
        complexity=2,
    ),
    FactorSpec(
        id="stochrsi14",
        name="StochRSI(14)",
        family="rsi",
        kind="stoch_rsi",
        params={"period": 14, "oversold": 20, "overbought": 80},
        description="Stochastic RSI mean reversion.",
        complexity=2,
    ),
    FactorSpec(
        id="rsi_div20",
        name="RSI bull/bear divergence",
        family="rsi",
        kind="rsi_divergence",
        params={"period": 14, "lookback": 20},
        description="Price vs RSI divergence.",
        complexity=3,
    ),
    FactorSpec(
        id="rsi_vol",
        name="RSI x volume confirmation",
        family="rsi",
        kind="rsi_volume",
        params={"period": 14, "oversold": 30, "overbought": 70},
        description="RSI extremes confirmed by above-average volume.",
        complexity=2,
    ),
]

BASELINE_ID = "rsi14_mr"


def is_rsi_family(spec: FactorSpec) -> bool:
    return spec.family == "rsi" and spec.kind != "noise"
