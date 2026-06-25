from pathlib import Path

import pandas as pd

from main import apply_backtest_preset
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
        fee_bps=10.0,
        slippage_bps=5.0,
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


def _stop_loss_history() -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=12, freq="D")
    close = [100, 100, 100, 100, 100, 100, 88, 90, 92, 94, 96, 98]
    return pd.DataFrame({"close": close, "volume": [1000] * 12}, index=index)


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
    assert not result.performance.empty
    assert {"notional", "fee"}.issubset(result.trades.columns)
    assert set(result.trades["direction"]).issubset({"BUY", "SELL"})


def test_backtest_presets_expand_windows():
    assert apply_backtest_preset("3m", 30, 7) == (140, 90)
    assert apply_backtest_preset("6m", 120, 30) == (220, 180)
    assert apply_backtest_preset(None, 120, 30) == (120, 30)


def test_stop_loss_does_not_rebuy_same_ticker_same_day():
    rankings = pd.DataFrame(
        [
            {"ticker": "AAA", "symbol": "AAAONUSDT", "price": 100, "reason": "test", "score": 90},
        ]
    )
    result = run_backtest(rankings, {"AAA": _stop_loss_history()}, _config(), days=12)
    trades = result.trades
    stop_sells = trades[(trades["direction"] == "SELL") & (trades["reason"] == "stop loss")]

    assert not stop_sells.empty
    for timestamp in stop_sells["timestamp"]:
        same_time = trades[trades["timestamp"] == timestamp]
        assert not ((same_time["ticker"] == "AAA") & (same_time["direction"] == "BUY")).any()
