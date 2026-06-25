from __future__ import annotations

import pandas as pd

from factors.category_leader import add_category_leader_score
from factors.macro_sentiment import neutral_macro_sentiment
from factors.momentum import momentum_metrics
from factors.technical import technical_score


def normalize_series(values: pd.Series) -> pd.Series:
    values = values.astype(float)
    if values.empty:
        return values
    low = values.min()
    high = values.max()
    if pd.isna(low) or pd.isna(high) or high == low:
        return pd.Series([50.0] * len(values), index=values.index)
    return (values - low) / (high - low) * 100.0


def build_score_table(
    universe: pd.DataFrame,
    histories: dict[str, pd.DataFrame],
    symbol_map: dict[str, str] | None = None,
    source_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    symbol_map = symbol_map or {}
    source_map = source_map or {}
    macro = neutral_macro_sentiment()
    rows: list[dict[str, object]] = []
    for item in universe.to_dict("records"):
        ticker = str(item["ticker"])
        history = histories.get(ticker)
        if history is None or history.empty:
            continue
        tech = technical_score(history)
        mom = momentum_metrics(history)
        last_close = float(history["close"].dropna().iloc[-1])
        last_date = history.index[-1]
        rows.append(
            {
                "ticker": ticker,
                "category": item["category"],
                "exchange": item["exchange"],
                "symbol": symbol_map.get(ticker, ticker),
                "source": source_map.get(ticker, "unknown"),
                "last_date": last_date,
                "price": last_close,
                **tech,
                **mom,
                **macro,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["momentum_score"] = normalize_series(frame["momentum_raw"])
    frame = add_category_leader_score(frame)
    frame["score"] = (
        0.25 * frame["technical_score"]
        + 0.25 * frame["momentum_score"]
        + 0.20 * frame["category_leader_score"]
        + 0.15 * frame["macro_score"]
        + 0.15 * frame["sentiment_score"]
    )
    frame["reason"] = frame.apply(_fallback_reason, axis=1)
    frame = frame.sort_values(["score", "momentum_score"], ascending=False).reset_index(drop=True)
    frame.insert(0, "rank", range(1, len(frame) + 1))
    return frame


def _fallback_reason(row: pd.Series) -> str:
    return (
        f"{row['source']} {row['symbol']} price {row['price']:.2f}; "
        f"20d return {row['return_20d']:.1%}; "
        f"category leadership {row['category_leader_score']:.0f}/100."
    )
