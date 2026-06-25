from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

try:
    import gradio as gr
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("gradio is not installed. Run: pip install -r requirements.txt") from exc

try:
    import plotly.express as px
except ModuleNotFoundError:  # pragma: no cover
    px = None

from main import run_pipeline
from trading.logger import load_trades
from utils.config import ROOT


RANKINGS_PATH = ROOT / "data/latest_rankings.csv"
EQUITY_PATH = ROOT / "data/equity_curve.csv"
TRADES_DB_PATH = ROOT / "data/trades.db"
TRADES_CSV_PATH = ROOT / "logs/trades.csv"
ERRORS_PATH = ROOT / "data/data_errors.csv"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _pnl_plot(equity: pd.DataFrame):
    if equity.empty or px is None:
        return None
    equity = equity.copy()
    equity["timestamp"] = pd.to_datetime(equity["timestamp"])
    return px.line(equity, x="timestamp", y="equity", title="Paper Trading Equity")


def _factor_plot(rankings: pd.DataFrame):
    if rankings.empty or px is None:
        return None
    cols = ["technical_score", "momentum_score", "category_leader_score", "macro_score", "sentiment_score"]
    top = rankings.head(10).melt(id_vars=["ticker"], value_vars=cols, var_name="factor", value_name="score")
    return px.bar(top, x="ticker", y="score", color="factor", barmode="group", title="Top 10 Factor Contribution")


def load_dashboard_data():
    rankings = _read_csv(RANKINGS_PATH)
    equity = _read_csv(EQUITY_PATH)
    errors = _read_csv(ERRORS_PATH)
    trades = load_trades(TRADES_DB_PATH)
    display_cols = [
        "rank",
        "ticker",
        "category",
        "symbol",
        "source",
        "price",
        "score",
        "technical_score",
        "momentum_score",
        "category_leader_score",
        "reason",
    ]
    if not rankings.empty:
        display_cols = [col for col in display_cols if col in rankings.columns]
        rankings_display = rankings[display_cols].head(30)
    else:
        rankings_display = rankings
    status = "Loaded cached outputs." if not rankings.empty else "No cached outputs yet. Run pipeline first."
    return status, rankings_display, _factor_plot(rankings), _pnl_plot(equity), trades.tail(50), errors, str(TRADES_CSV_PATH)


def run_dashboard_pipeline(limit: int, history_days: int, backtest_days: int, use_llm: bool):
    result = run_pipeline(
        limit=int(limit),
        history_days=int(history_days),
        backtest_days=int(backtest_days),
        use_llm=bool(use_llm),
        reset_logs=True,
    )
    status = (
        f"Run complete: {len(result.rankings)} rankings, "
        f"{len(result.backtest.trades)} trades, "
        f"{len(result.history_result.errors)} data errors."
    )
    rankings = result.rankings.head(30)
    trades = load_trades(TRADES_DB_PATH).tail(50)
    errors = _read_csv(ROOT / "data/data_errors.csv")
    return status, rankings, _factor_plot(result.rankings), _pnl_plot(result.backtest.equity_curve), trades, errors, str(result.trades_csv_path)


def build_app():
    with gr.Blocks(title="AI Hybrid Signal Engine") as demo:
        gr.Markdown("# AI Hybrid Signal Engine")
        with gr.Row():
            limit = gr.Slider(5, 211, value=24, step=1, label="Ticker Limit")
            history_days = gr.Slider(30, 240, value=120, step=10, label="History Days")
            backtest_days = gr.Slider(7, 90, value=30, step=1, label="Backtest Days")
            use_llm = gr.Checkbox(value=True, label="Use DeepSeek")
        with gr.Row():
            run_btn = gr.Button("Run Pipeline", variant="primary")
            refresh_btn = gr.Button("Refresh Cached")
        status = gr.Textbox(label="Status", interactive=False)
        rankings = gr.Dataframe(label="Rankings", interactive=False)
        factor_plot = gr.Plot(label="Factor Contribution")
        pnl_plot = gr.Plot(label="Paper Trading PnL")
        trades = gr.Dataframe(label="Recent Trades", interactive=False)
        errors = gr.Dataframe(label="Skipped / Data Errors", interactive=False)
        download = gr.File(label="Download trades.csv", interactive=False)

        outputs = [status, rankings, factor_plot, pnl_plot, trades, errors, download]
        run_btn.click(run_dashboard_pipeline, inputs=[limit, history_days, backtest_days, use_llm], outputs=outputs)
        refresh_btn.click(load_dashboard_data, outputs=outputs)
        demo.load(load_dashboard_data, outputs=outputs)
    return demo


if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("GRADIO_SERVER_PORT", "7860")))
    share = os.environ.get("GRADIO_SHARE", "false").lower() in {"1", "true", "yes", "on"}
    build_app().launch(server_name="0.0.0.0", server_port=port, share=share)
