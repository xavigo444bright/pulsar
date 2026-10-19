from __future__ import annotations

import numpy as np


def rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    close = np.asarray(close, dtype=float)
    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = np.zeros_like(close)
    avg_loss = np.zeros_like(close)
    if len(close) <= period:
        return np.full_like(close, 50.0)
    avg_gain[period] = gain[1 : period + 1].mean()
    avg_loss[period] = loss[1 : period + 1].mean()
    for i in range(period + 1, len(close)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i]) / period
    rs = np.divide(avg_gain, np.where(avg_loss == 0, np.nan, avg_loss))
    out = 100.0 - (100.0 / (1.0 + rs))
    out[:period] = 50.0
    return np.nan_to_num(out, nan=50.0)


def rsi_slope(close: np.ndarray, period: int = 14, lookback: int = 5) -> np.ndarray:
    values = rsi(close, period)
    slope = np.zeros_like(values)
    slope[lookback:] = values[lookback:] - values[:-lookback]
    return slope


def stoch_rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    values = rsi(close, period)
    out = np.full_like(values, 50.0)
    for i in range(period, len(values)):
        window = values[i - period + 1 : i + 1]
        lo, hi = window.min(), window.max()
        out[i] = 50.0 if hi == lo else 100.0 * (values[i] - lo) / (hi - lo)
    return out


def rolling_mean(x: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return x.copy()
    c = np.cumsum(x)
    out = np.empty_like(x)
    out[: window - 1] = x[: window - 1]
    out[window - 1 :] = (c[window - 1 :] - np.concatenate(([0], c[:-window]))) / window
    return out
