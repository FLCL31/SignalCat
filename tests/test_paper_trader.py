from pathlib import Path

import pandas as pd

from trading.paper_trader import run_backtest
from utils.config import AppConfig


def _config() -> AppConfig:
    return AppConfig(
        root=Path("."),
        data_source="bitget",
        yfinance_fallback=False,
        initial_cash=10000,
        top_n=2,
        max_position_pct=0.2,
        stop_loss_pct=-0.05,
        deepseek_api_key="",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        bitget_api_key="",
        bitget_api_secret="",
        bitget_api_passphrase="",
        bitget_base_url="https://api.bitget.com",
        bitget_enabled=True,
        bitget_stock_symbol_suffix="ONUSDT",
    )


def _history(mult: float) -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=45, freq="D")
    close = [100 + i * mult for i in range(45)]
    return pd.DataFrame({"close": close, "volume": [1000] * 45}, index=index)


def test_run_backtest_generates_trades():
    rankings = pd.DataFrame(
        [
            {"ticker": "AAA", "symbol": "AAAONUSDT", "price": 120, "reason": "test", "score": 90},
            {"ticker": "BBB", "symbol": "BBBONUSDT", "price": 110, "reason": "test", "score": 80},
            {"ticker": "CCC", "symbol": "CCCONUSDT", "price": 105, "reason": "test", "score": 70},
        ]
    )
    result = run_backtest(rankings, {"AAA": _history(1), "BBB": _history(0.5), "CCC": _history(0.2)}, _config(), days=20)
    assert not result.trades.empty
    assert not result.equity_curve.empty
    assert set(result.trades["direction"]).issubset({"BUY", "SELL"})
