from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BacktestResult:
    equity: np.ndarray
    returns: np.ndarray
    sharpe: float
    turnover: float
    max_drawdown: float
    trades: int
    bars: int


def run_signal(
    close: np.ndarray,
    signal: np.ndarray,
    fee_bps: float,
    next_bar: bool = True,
) -> BacktestResult:
    close = np.asarray(close, dtype=float)
    signal = np.asarray(signal, dtype=float)
    if next_bar:
        pos = np.roll(signal, 1)
        pos[0] = 0.0
    else:
        pos = signal
    ret = np.diff(close, prepend=close[0]) / np.where(close == 0, 1, close)
    ret[0] = 0.0
    turnover = np.abs(np.diff(pos, prepend=0.0))
    cost = turnover * (fee_bps / 10_000)
    strat = pos * ret - cost
    equity = np.cumprod(1.0 + strat)
    sharpe = _sharpe(strat)
    dd = _max_drawdown(equity)
    trades = int(np.sum(turnover > 0))
    return BacktestResult(
        equity=equity,
        returns=strat,
        sharpe=float(sharpe),
        turnover=float(turnover.mean()),
        max_drawdown=float(dd),
        trades=trades,
        bars=len(close),
    )


def walk_forward(
    close: np.ndarray,
    signal: np.ndarray,
    fee_bps: float,
    folds: int = 3,
) -> list[BacktestResult]:
    n = len(close)
    fold = n // folds
    results: list[BacktestResult] = []
    for i in range(folds):
        start = i * fold
        end = n if i == folds - 1 else (i + 1) * fold
        if end - start < 50:
            continue
        results.append(run_signal(close[start:end], signal[start:end], fee_bps))
    return results


def _sharpe(returns: np.ndarray) -> float:
    if returns.std() == 0:
        return 0.0
    return float(np.sqrt(24 * 365) * returns.mean() / returns.std())  # hourly-ish


def _max_drawdown(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    dd = (peak - equity) / np.where(peak == 0, 1, peak)
    return float(dd.max()) if len(dd) else 0.0
