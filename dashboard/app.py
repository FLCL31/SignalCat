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

from main import apply_backtest_preset, run_pipeline
from trading.logger import load_trades
from utils.config import ROOT


RANKINGS_PATH = ROOT / "data/latest_rankings.csv"
EQUITY_PATH = ROOT / "data/equity_curve.csv"
PERFORMANCE_PATH = ROOT / "data/performance_summary.csv"
TRADES_DB_PATH = ROOT / "data/trades.db"
TRADES_CSV_PATH = ROOT / "logs/trades.csv"
ERRORS_PATH = ROOT / "data/data_errors.csv"


CSS = """
.app-shell {max-width: 1440px; margin: 0 auto;}
.hero {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 18px 20px;
  background: #ffffff;
}
.hero h1 {font-size: 28px; line-height: 1.15; margin: 0 0 6px;}
.hero p {margin: 0; color: #4b5563;}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 12px 0;
}
.metric-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px 14px;
  background: #ffffff;
}
.metric-label {font-size: 12px; color: #6b7280; margin-bottom: 4px;}
.metric-value {font-size: 24px; font-weight: 700; color: #111827;}
.metric-note {font-size: 12px; color: #6b7280; margin-top: 2px;}
.control-panel {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  background: #f9fafb;
}
"""

THEME = gr.themes.Soft(primary_hue="blue", neutral_hue="slate")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _pnl_plot(equity: pd.DataFrame):
    if equity.empty or px is None:
        return None
    equity = equity.copy()
    equity["timestamp"] = pd.to_datetime(equity["timestamp"])
    fig = px.line(equity, x="timestamp", y="equity", title="Paper Trading Equity", template="plotly_white")
    fig.update_traces(line_color="#2563eb", line_width=2.5)
    fig.update_layout(margin=dict(l=20, r=20, t=48, b=20), height=340)
    return fig


def _factor_plot(rankings: pd.DataFrame):
    if rankings.empty or px is None:
        return None
    cols = ["technical_score", "momentum_score", "category_leader_score", "macro_score", "sentiment_score"]
    top = rankings.head(10).melt(id_vars=["ticker"], value_vars=cols, var_name="factor", value_name="factor_score")
    fig = px.bar(
        top,
        x="ticker",
        y="factor_score",
        color="factor",
        barmode="group",
        title="Top 10 Factor Contribution",
        template="plotly_white",
        color_discrete_sequence=["#2563eb", "#059669", "#f59e0b", "#7c3aed", "#dc2626"],
    )
    fig.update_layout(margin=dict(l=20, r=20, t=48, b=20), height=360, legend_title_text="")
    return fig


def _performance_value(performance: pd.DataFrame, metric: str, default: str = "--") -> str:
    if performance.empty or "metric" not in performance or "value" not in performance:
        return default
    rows = performance.loc[performance["metric"] == metric, "value"]
    if rows.empty:
        return default
    value = float(rows.iloc[0])
    if metric in {"Total Return", "Annualized Return", "Max Drawdown"}:
        return f"{value:.2%}"
    if metric in {"Sharpe"}:
        return f"{value:.2f}"
    if metric in {"Trade Count"}:
        return f"{int(value)}"
    return f"{value:.2f}"


def _metrics_html(rankings: pd.DataFrame, equity: pd.DataFrame, trades: pd.DataFrame, errors: pd.DataFrame, performance: pd.DataFrame) -> str:
    top_score = "--"
    top_ticker = "No ranking"
    if not rankings.empty:
        top_score = f"{float(rankings.iloc[0]['score']):.1f}"
        top_ticker = str(rankings.iloc[0]["ticker"])
    total_return = _performance_value(performance, "Total Return")
    max_drawdown = _performance_value(performance, "Max Drawdown")
    sharpe = _performance_value(performance, "Sharpe")
    trade_count = _performance_value(performance, "Trade Count", str(len(trades)))
    skipped = len(errors)
    return f"""
<div class="metric-grid">
  <div class="metric-card"><div class="metric-label">Top Signal</div><div class="metric-value">{top_ticker}</div><div class="metric-note">Score {top_score}</div></div>
  <div class="metric-card"><div class="metric-label">Total Return</div><div class="metric-value">{total_return}</div><div class="metric-note">Paper backtest</div></div>
  <div class="metric-card"><div class="metric-label">Max Drawdown</div><div class="metric-value">{max_drawdown}</div><div class="metric-note">Equity curve risk</div></div>
  <div class="metric-card"><div class="metric-label">Sharpe</div><div class="metric-value">{sharpe}</div><div class="metric-note">{trade_count} trades, {skipped} skipped</div></div>
</div>
"""


def load_dashboard_data():
    rankings = _read_csv(RANKINGS_PATH)
    equity = _read_csv(EQUITY_PATH)
    performance = _read_csv(PERFORMANCE_PATH)
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
    return status, _metrics_html(rankings, equity, trades, errors, performance), rankings_display, _factor_plot(rankings), _pnl_plot(equity), trades.tail(50), performance, errors, str(TRADES_CSV_PATH)


def run_dashboard_pipeline(limit: int, preset: str, history_days: int, backtest_days: int, use_llm: bool):
    preset_key = {"Custom": None, "3 Months": "3m", "6 Months": "6m"}.get(preset)
    history_days, backtest_days = apply_backtest_preset(preset_key, int(history_days), int(backtest_days))
    result = run_pipeline(
        limit=int(limit),
        history_days=history_days,
        backtest_days=backtest_days,
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
    return status, _metrics_html(result.rankings, result.backtest.equity_curve, trades, errors, result.backtest.performance), rankings, _factor_plot(result.rankings), _pnl_plot(result.backtest.equity_curve), trades, result.backtest.performance, errors, str(result.trades_csv_path)


def build_app():
    with gr.Blocks(title="SignalCat") as demo:
        with gr.Column(elem_classes=["app-shell"]):
            gr.HTML(
                """
<div class="hero">
  <h1>SignalCat</h1>
  <p>Bitget-first AI stock-chain ranking, DeepSeek signal rationale, and paper-trading audit logs.</p>
</div>
"""
            )
            with gr.Group(elem_classes=["control-panel"]):
                with gr.Row():
                    limit = gr.Slider(5, 211, value=24, step=1, label="Ticker Limit")
                    preset = gr.Radio(["Custom", "3 Months", "6 Months"], value="Custom", label="Backtest Preset")
                    history_days = gr.Slider(30, 240, value=120, step=10, label="History Days")
                    backtest_days = gr.Slider(7, 180, value=30, step=1, label="Backtest Days")
                    use_llm = gr.Checkbox(value=True, label="Use DeepSeek")
                with gr.Row():
                    run_btn = gr.Button("Run Pipeline", variant="primary")
                    refresh_btn = gr.Button("Refresh Cached")
            status = gr.Textbox(label="Status", interactive=False)
            metrics = gr.HTML()
            with gr.Tabs():
                with gr.Tab("Overview"):
                    rankings = gr.Dataframe(label="Rankings", interactive=False, wrap=True)
                    factor_plot = gr.Plot(label="Factor Contribution")
                with gr.Tab("Trading"):
                    pnl_plot = gr.Plot(label="Paper Trading PnL")
                    performance = gr.Dataframe(label="Performance Summary", interactive=False, wrap=True)
                    trades = gr.Dataframe(label="Recent Trades", interactive=False, wrap=True)
                    download = gr.File(label="Download trades.csv", interactive=False)
                with gr.Tab("Coverage"):
                    errors = gr.Dataframe(label="Skipped / Data Errors", interactive=False, wrap=True)

        outputs = [status, metrics, rankings, factor_plot, pnl_plot, trades, performance, errors, download]
        run_btn.click(run_dashboard_pipeline, inputs=[limit, preset, history_days, backtest_days, use_llm], outputs=outputs)
        refresh_btn.click(load_dashboard_data, outputs=outputs)
        demo.load(load_dashboard_data, outputs=outputs)
    return demo


if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("GRADIO_SERVER_PORT", "7860")))
    share = os.environ.get("GRADIO_SHARE", "false").lower() in {"1", "true", "yes", "on"}
    build_app().launch(server_name="0.0.0.0", server_port=port, share=share, theme=THEME, css=CSS)
