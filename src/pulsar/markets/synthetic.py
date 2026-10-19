"""Deterministic OHLCV so clone-and-run needs no exchange keys."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from pulsar.ports.market import Bar

SPECS = {
    "BTCUSDT": {"start": 40_000.0, "vol": 0.012, "mr": 0.08, "seed": 7},
    "SPY": {"start": 430.0, "vol": 0.007, "mr": 0.12, "seed": 11},
    "QQQ": {"start": 380.0, "vol": 0.009, "mr": 0.10, "seed": 13},
    "MES": {"start": 5200.0, "vol": 0.008, "mr": 0.11, "seed": 17},
    "ES": {"start": 5200.0, "vol": 0.008, "mr": 0.11, "seed": 19},
}


def generate_bars(symbol: str, n: int = 800, timeframe: str = "1h") -> list[Bar]:
    spec = SPECS.get(symbol.upper(), {"start": 100.0, "vol": 0.01, "mr": 0.05, "seed": 1})
    rng = np.random.default_rng(spec["seed"])
    dt = _delta(timeframe)
    start = datetime(2022, 1, 3, tzinfo=timezone.utc)
    price = float(spec["start"])
    mean = price
    bars: list[Bar] = []
    for i in range(n):
        shock = rng.normal(0, spec["vol"])
        price = price + spec["mr"] * (mean - price) + price * shock
        price = max(price, 0.01)
        intra = abs(rng.normal(0, spec["vol"] * 0.4))
        high = price * (1 + intra)
        low = price * (1 - intra)
        open_px = price * (1 + rng.normal(0, spec["vol"] * 0.15))
        volume = float(abs(rng.normal(1_000, 200)))
        ts = start + dt * i
        bars.append(
            Bar(
                ts=ts,
                open=float(open_px),
                high=float(max(high, open_px, price)),
                low=float(min(low, open_px, price)),
                close=float(price),
                volume=volume,
            )
        )
    return bars


def bars_to_arrays(bars: list[Bar]) -> dict[str, np.ndarray]:
    return {
        "open": np.array([b.open for b in bars], dtype=float),
        "high": np.array([b.high for b in bars], dtype=float),
        "low": np.array([b.low for b in bars], dtype=float),
        "close": np.array([b.close for b in bars], dtype=float),
        "volume": np.array([b.volume for b in bars], dtype=float),
    }


def _delta(timeframe: str) -> timedelta:
    if timeframe.endswith("h"):
        return timedelta(hours=int(timeframe[:-1] or 1))
    if timeframe.endswith("d"):
        return timedelta(days=int(timeframe[:-1] or 1))
    if timeframe.endswith("m"):
        return timedelta(minutes=int(timeframe[:-1] or 1))
    return timedelta(hours=1)
