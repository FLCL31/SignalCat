from __future__ import annotations

import pandas as pd


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def rsi(close: pd.Series, window: int = 14) -> float:
    close = close.dropna()
    if len(close) < window + 1:
        return 50.0
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = -delta.clip(upper=0).rolling(window).mean()
    rs = gain / loss.replace(0, pd.NA)
    value = 100 - (100 / (1 + rs.iloc[-1]))
    if pd.isna(value):
        return 50.0
    return float(value)


def technical_score(history: pd.DataFrame) -> dict[str, float]:
    close = history["close"].dropna()
    volume = history["volume"].dropna() if "volume" in history else pd.Series(dtype=float)
    if close.empty:
        return {"rsi": 50.0, "trend_score": 50.0, "volume_score": 50.0, "technical_score": 50.0}

    rsi_value = rsi(close)
    sma_fast = close.tail(5).mean()
    sma_slow = close.tail(min(len(close), 20)).mean()
    trend_pct = 0.0 if sma_slow == 0 else (sma_fast / sma_slow - 1.0)
    trend = clamp(50.0 + trend_pct * 500.0)

    if len(volume) >= 6:
        recent_volume = volume.tail(3).mean()
        base_volume = volume.tail(min(len(volume), 20)).mean()
        volume_pct = 0.0 if base_volume == 0 else recent_volume / base_volume - 1.0
        volume_score = clamp(50.0 + volume_pct * 80.0)
    else:
        volume_score = 50.0

    # Prefer strong trend with RSI that is not extremely overbought.
    rsi_balance = clamp(100.0 - abs(rsi_value - 58.0) * 2.2)
    combined = clamp(0.45 * trend + 0.35 * rsi_balance + 0.20 * volume_score)
    return {
        "rsi": rsi_value,
        "trend_score": trend,
        "volume_score": volume_score,
        "technical_score": combined,
    }
