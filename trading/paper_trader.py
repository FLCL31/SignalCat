from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from utils.config import AppConfig


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    performance: pd.DataFrame


def run_backtest(
    rankings: pd.DataFrame,
    histories: dict[str, pd.DataFrame],
    config: AppConfig,
    days: int = 30,
) -> BacktestResult:
    if rankings.empty:
        return BacktestResult(_empty_trades(), _empty_equity(), _empty_performance())

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

        stopped_today: set[str] = set()
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
            cash += _sell(ticker, date, float(current[ticker]), positions, trades, rank_meta, config, "stop loss")
            entry_prices.pop(ticker, None)
            stopped_today.add(ticker)

        momentum = (current[common] / previous[common] - 1.0).sort_values(ascending=False)
        target = set(momentum.head(top_n).index)

        for ticker in list(positions):
            if ticker not in target and ticker in current.index and not pd.isna(current[ticker]):
                cash += _sell(ticker, date, float(current[ticker]), positions, trades, rank_meta, config, "rebalance")
                entry_prices.pop(ticker, None)

        equity = cash + sum(qty * float(current.get(ticker, 0.0)) for ticker, qty in positions.items())
        for ticker in target:
            if ticker in stopped_today or ticker in positions or ticker not in current.index or pd.isna(current[ticker]):
                continue
            price = float(current[ticker])
            allocation = min(config.max_position_pct * equity, cash)
            if allocation <= 0 or price <= 0:
                continue
            execution_price = _buy_price(price, config)
            fee_rate = _cost_rate(config)
            notional = allocation / (1.0 + fee_rate)
            cost = notional * fee_rate
            qty = notional / execution_price
            cash -= notional + cost
            positions[ticker] = qty
            entry_prices[ticker] = execution_price
            meta = rank_meta.get(ticker, {})
            trades.append(
                {
                    "timestamp": date,
                    "ticker": ticker,
                    "symbol": meta.get("symbol", ticker),
                    "direction": "BUY",
                    "price": execution_price,
                    "quantity": qty,
                    "balance_change": -(notional + cost),
                    "notional": notional,
                    "fee": cost,
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
    return BacktestResult(trades_frame, equity_frame, summarize_performance(equity_frame, trades_frame, config))


def run_latest_paper_trades(rankings: pd.DataFrame, config: AppConfig) -> BacktestResult:
    trades: list[dict[str, object]] = []
    cash = config.initial_cash
    timestamp = pd.Timestamp.utcnow().tz_localize(None)
    for row in rankings.head(config.top_n).to_dict("records"):
        price = float(row["price"])
        allocation = min(config.max_position_pct * config.initial_cash, cash)
        if allocation <= 0 or price <= 0:
            continue
        execution_price = _buy_price(price, config)
        fee_rate = _cost_rate(config)
        notional = allocation / (1.0 + fee_rate)
        cost = notional * fee_rate
        quantity = notional / execution_price
        cash -= notional + cost
        trades.append(
            {
                "timestamp": timestamp,
                "ticker": row["ticker"],
                "symbol": row.get("symbol", row["ticker"]),
                "direction": "BUY",
                "price": execution_price,
                "quantity": quantity,
                "balance_change": -(notional + cost),
                "notional": notional,
                "fee": cost,
                "reason": row.get("reason", "latest top ranking"),
            }
        )
    equity = config.initial_cash
    trades_frame = pd.DataFrame(trades)
    equity_frame = pd.DataFrame([{"timestamp": timestamp, "equity": equity, "cash": cash}])
    return BacktestResult(trades_frame, equity_frame, summarize_performance(equity_frame, trades_frame, config))


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
    config: AppConfig,
    reason: str,
) -> float:
    qty = positions.pop(ticker)
    execution_price = _sell_price(price, config)
    gross = qty * execution_price
    cost = gross * _cost_rate(config)
    proceeds = gross - cost
    meta = rank_meta.get(ticker, {})
    trades.append(
        {
            "timestamp": date,
            "ticker": ticker,
            "symbol": meta.get("symbol", ticker),
            "direction": "SELL",
            "price": execution_price,
            "quantity": qty,
            "balance_change": proceeds,
            "notional": gross,
            "fee": cost,
            "reason": reason,
        }
    )
    return proceeds


def _cost_rate(config: AppConfig) -> float:
    return max(config.fee_bps, 0.0) / 10000.0


def _slippage_rate(config: AppConfig) -> float:
    return max(config.slippage_bps, 0.0) / 10000.0


def _buy_price(price: float, config: AppConfig) -> float:
    return price * (1.0 + _slippage_rate(config))


def _sell_price(price: float, config: AppConfig) -> float:
    return price * (1.0 - _slippage_rate(config))


def summarize_performance(equity: pd.DataFrame, trades: pd.DataFrame, config: AppConfig) -> pd.DataFrame:
    if equity.empty or "equity" not in equity:
        return _empty_performance()
    series = equity["equity"].astype(float)
    start = float(series.iloc[0])
    end = float(series.iloc[-1])
    returns = series.pct_change().dropna()
    total_return = 0.0 if start == 0 else end / start - 1.0
    max_drawdown = 0.0
    if not series.empty:
        running_max = series.cummax()
        drawdown = series / running_max - 1.0
        max_drawdown = float(drawdown.min())
    sharpe = 0.0
    if len(returns) > 1 and float(returns.std()) != 0.0:
        sharpe = float((returns.mean() / returns.std()) * (252 ** 0.5))
    days = len(series)
    annualized_return = 0.0
    if days > 1 and start > 0 and end > 0:
        annualized_return = float((end / start) ** (252 / days) - 1.0)
    trade_count = len(trades)
    total_fees = float(trades["fee"].sum()) if not trades.empty and "fee" in trades else 0.0
    return pd.DataFrame(
        [
            {"metric": "Initial Cash", "value": config.initial_cash},
            {"metric": "Ending Equity", "value": end},
            {"metric": "Total Return", "value": total_return},
            {"metric": "Annualized Return", "value": annualized_return},
            {"metric": "Max Drawdown", "value": max_drawdown},
            {"metric": "Sharpe", "value": sharpe},
            {"metric": "Trade Count", "value": trade_count},
            {"metric": "Total Fees", "value": total_fees},
            {"metric": "Fee Bps", "value": config.fee_bps},
            {"metric": "Slippage Bps", "value": config.slippage_bps},
        ]
    )


def _empty_trades() -> pd.DataFrame:
    return pd.DataFrame(columns=["timestamp", "ticker", "symbol", "direction", "price", "quantity", "balance_change", "notional", "fee", "reason"])


def _empty_equity() -> pd.DataFrame:
    return pd.DataFrame(columns=["timestamp", "equity", "cash"])


def _empty_performance() -> pd.DataFrame:
    return pd.DataFrame(columns=["metric", "value"])
