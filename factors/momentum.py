from __future__ import annotations

import math

import pandas as pd


def _return(close: pd.Series, periods: int) -> float:
    if len(close) <= periods:
        return 0.0
    start = close.iloc[-periods - 1]
    end = close.iloc[-1]
    if start == 0:
        return 0.0
    return float(end / start - 1.0)


def momentum_metrics(history: pd.DataFrame) -> dict[str, float]:
    close = history["close"].dropna()
    if len(close) < 2:
        return {"return_5d": 0.0, "return_20d": 0.0, "volatility_20d": 0.0, "momentum_raw": 0.0}
    returns = close.pct_change().dropna()
    volatility = float(returns.tail(min(20, len(returns))).std() * math.sqrt(252)) if not returns.empty else 0.0
    ret_5 = _return(close, 5)
    ret_20 = _return(close, 20)
    momentum_raw = 0.65 * ret_20 + 0.35 * ret_5 - 0.08 * volatility
    return {
        "return_5d": ret_5,
        "return_20d": ret_20,
        "volatility_20d": volatility,
        "momentum_raw": momentum_raw,
    }
