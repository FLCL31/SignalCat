from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from utils.config import AppConfig


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    equity_curve: pd.DataFrame


def run_backtest(
    rankings: pd.DataFrame,
    histories: dict[str, pd.DataFrame],
    config: AppConfig,
    days: int = 30,
) -> BacktestResult:
    if rankings.empty:
        return BacktestResult(_empty_trades(), _empty_equity())

    tickers = rankings["ticker"].tolist()
    panel = _build_close_panel(tickers, histories)
    if panel.empty or len(panel) < 8:
        return run_latest_paper_trades(rankings, config)

    panel = panel.tail(max(days + 25, 30)).dropna(how="all")
    cash = config.initial_cash
    positions: dict[str, float] = {}
    entry_prices: dict[str, float] = {}
    trades: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []
    rank_meta = rankings.set_index("ticker").to_dict("index")
    top_n = max(1, config.top_n)

    for idx in range(5, len(panel)):
        date = panel.index[idx]
        current = panel.iloc[idx].dropna()
        previous = panel.iloc[idx - 5].dropna()
        common = current.index.intersection(previous.index)
        if common.empty:
            continue

        equity = cash + sum(qty * float(current.get(ticker, 0.0)) for ticker, qty in positions.items())
        equity_rows.append({"timestamp": date, "equity": equity, "cash": cash})

        stop_tickers = []
        for ticker, qty in positions.items():
            price = current.get(ticker)
            entry = entry_prices.get(ticker)
            if price is None or pd.isna(price) or not entry:
                continue
            if float(price) / entry - 1.0 <= config.stop_loss_pct:
                stop_tickers.append(ticker)
        for ticker in stop_tickers:
            cash += _sell(ticker, date, float(current[ticker]), positions, trades, rank_meta, "stop loss")

        momentum = (current[common] / previous[common] - 1.0).sort_values(ascending=False)
        target = set(momentum.head(top_n).index)

        for ticker in list(positions):
            if ticker not in target and ticker in current.index and not pd.isna(current[ticker]):
                cash += _sell(ticker, date, float(current[ticker]), positions, trades, rank_meta, "rebalance")

        equity = cash + sum(qty * float(current.get(ticker, 0.0)) for ticker, qty in positions.items())
        for ticker in target:
            if ticker in positions or ticker not in current.index or pd.isna(current[ticker]):
                continue
            price = float(current[ticker])
            allocation = min(config.max_position_pct * equity, cash)
            if allocation <= 0 or price <= 0:
                continue
            qty = allocation / price
            cash -= allocation
            positions[ticker] = qty
            entry_prices[ticker] = price
            meta = rank_meta.get(ticker, {})
            trades.append(
                {
                    "timestamp": date,
                    "ticker": ticker,
                    "symbol": meta.get("symbol", ticker),
                    "direction": "BUY",
                    "price": price,
                    "quantity": qty,
                    "balance_change": -allocation,
                    "reason": meta.get("reason", "daily momentum entry"),
                }
            )

    if not panel.empty:
        last_date = panel.index[-1]
        last_prices = panel.iloc[-1]
        equity = cash + sum(
            qty * float(last_prices.get(ticker, 0.0))
            for ticker, qty in positions.items()
            if not pd.isna(last_prices.get(ticker, pd.NA))
        )
        equity_rows.append({"timestamp": last_date, "equity": equity, "cash": cash})

    trades_frame = pd.DataFrame(trades)
    equity_frame = pd.DataFrame(equity_rows).drop_duplicates(subset=["timestamp"], keep="last")
    if trades_frame.empty:
        return run_latest_paper_trades(rankings, config)
    return BacktestResult(trades_frame, equity_frame)


def run_latest_paper_trades(rankings: pd.DataFrame, config: AppConfig) -> BacktestResult:
    trades: list[dict[str, object]] = []
    cash = config.initial_cash
    timestamp = pd.Timestamp.utcnow().tz_localize(None)
    for row in rankings.head(config.top_n).to_dict("records"):
        price = float(row["price"])
        allocation = min(config.max_position_pct * config.initial_cash, cash)
        if allocation <= 0 or price <= 0:
            continue
        quantity = allocation / price
        cash -= allocation
        trades.append(
            {
                "timestamp": timestamp,
                "ticker": row["ticker"],
                "symbol": row.get("symbol", row["ticker"]),
                "direction": "BUY",
                "price": price,
                "quantity": quantity,
                "balance_change": -allocation,
                "reason": row.get("reason", "latest top ranking"),
            }
        )
    equity = config.initial_cash
    return BacktestResult(pd.DataFrame(trades), pd.DataFrame([{"timestamp": timestamp, "equity": equity, "cash": cash}]))


def _build_close_panel(tickers: list[str], histories: dict[str, pd.DataFrame]) -> pd.DataFrame:
    series = {}
    for ticker in tickers:
        history = histories.get(ticker)
        if history is None or history.empty or "close" not in history:
            continue
        series[ticker] = history["close"].astype(float)
    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series).sort_index().ffill()


def _sell(
    ticker: str,
    date: pd.Timestamp,
    price: float,
    positions: dict[str, float],
    trades: list[dict[str, object]],
    rank_meta: dict[str, dict[str, object]],
    reason: str,
) -> float:
    qty = positions.pop(ticker)
    proceeds = qty * price
    meta = rank_meta.get(ticker, {})
    trades.append(
        {
            "timestamp": date,
            "ticker": ticker,
            "symbol": meta.get("symbol", ticker),
            "direction": "SELL",
            "price": price,
            "quantity": qty,
            "balance_change": proceeds,
            "reason": reason,
        }
    )
    return proceeds


def _empty_trades() -> pd.DataFrame:
    return pd.DataFrame(columns=["timestamp", "ticker", "symbol", "direction", "price", "quantity", "balance_change", "reason"])


def _empty_equity() -> pd.DataFrame:
    return pd.DataFrame(columns=["timestamp", "equity", "cash"])
