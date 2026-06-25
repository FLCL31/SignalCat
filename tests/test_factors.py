import pandas as pd

from utils.scoring import build_score_table


def _history(start: float, step: float) -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=40, freq="D")
    close = [start + i * step for i in range(40)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [x * 1.01 for x in close],
            "low": [x * 0.99 for x in close],
            "close": close,
            "volume": [1000 + i * 10 for i in range(40)],
        },
        index=index,
    )


def test_build_score_table_ranks_rows():
    universe = pd.DataFrame(
        [
            {"index": 1, "category": "A", "ticker": "AAA", "exchange": "NYSE"},
            {"index": 2, "category": "A", "ticker": "BBB", "exchange": "NASDAQ"},
        ]
    )
    histories = {"AAA": _history(10, 1), "BBB": _history(10, 0.1)}
    rankings = build_score_table(universe, histories, {"AAA": "AAAONUSDT", "BBB": "BBBONUSDT"})
    assert list(rankings["ticker"]) == ["AAA", "BBB"]
    assert rankings["score"].between(0, 100).all()
    assert "reason" in rankings.columns
