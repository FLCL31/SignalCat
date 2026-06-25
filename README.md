# SignalForge AI Stocks

SignalForge AI Stocks is a Bitget-first AI stock signal engine for the Bitget AI Hackathon Track 3. It turns a static TradingView watchlist of 211 US-listed AI infrastructure and application stocks into ranked signals, DeepSeek-generated reasoning, and reproducible paper-trading records.

The project is paper-only. It does not place real orders or require live account funds.

## Hackathon Thesis

AI equity traders often start with a broad watchlist, but the hard part is deciding which names deserve attention today. This project converts a 211-stock AI industry-chain universe across 24 categories into a repeatable decision workflow:

1. Map each stock ticker to a Bitget spot stock-token symbol.
2. Pull Bitget daily candles.
3. Compute technical, momentum, volatility, and category leadership factors.
4. Ask DeepSeek to turn the highest-ranked signals into concise investment rationales.
5. Run a configurable paper-trading backtest and save auditable logs.
6. Show the results in a Gradio dashboard for judges and users.

This makes a static AI-stock list actionable while keeping the output verifiable through CSV, SQLite, and generated backtest reports.

## Core Features

- **211-stock AI universe**: parses `LIST.md` into `data/universe.csv`, covering 24 AI industry categories.
- **Bitget-first data source**: resolves symbols such as `NVDA -> NVDAONUSDT`, `INTC -> RINTCUSDT`, and skips unsupported tickers by default.
- **No silent fallback**: `YFINANCE_FALLBACK=false` by default, so rankings are based on Bitget data unless explicitly changed.
- **Symbol coverage report**: writes `data/bitget_symbol_coverage.csv`; run `python3 main.py check-symbols` for full-universe coverage or `--limit` for a lightweight sample.
- **Multi-factor ranking**: combines RSI/trend/volume, 5d and 20d momentum, volatility adjustment, category leadership, and neutral macro/sentiment placeholders.
- **DeepSeek rationale layer**: generates concise top-signal explanations and an overall market thesis when `DEEPSEEK_API_KEY` is configured.
- **Deterministic fallback**: keeps the pipeline runnable even without DeepSeek.
- **Paper-trading engine**: supports initial cash, top-N allocation, max position size, stop loss, daily rebalance, fees, and slippage.
- **Backtest presets**: `3m` and `6m` presets are available from CLI and dashboard.
- **Audit logs**: writes rankings, equity curve, performance summary, skipped ticker errors, SQLite trades, CSV trades, and a Markdown report.
- **Gradio dashboard**: provides an interactive UI for running the pipeline, inspecting rankings, factor contribution, paper PnL, trades, and data coverage.
- **Deployment scaffold**: includes root `app.py`, `Procfile`, `render.yaml`, and `.env.example`.

## Current Verification Snapshot

Latest committed sample backtest report:

```bash
python3 main.py run --limit 3 --history-days 60 --backtest-days 14
```

Generated:

- 3 ranked Bitget-supported tickers.
- 11 paper-trading rows.
- Ending equity: `10062.29` from `10000.00` simulated USDT.
- Total return: `0.62%`.
- Max drawdown: `-9.79%`.
- Sharpe: `0.31`.
- Fees/slippage included: `FEE_BPS=10`, `SLIPPAGE_BPS=5`.

Sample artifacts:

- `data/latest_rankings.csv`
- `data/equity_curve.csv`
- `data/performance_summary.csv`
- `data/data_errors.csv`
- `logs/trades.csv`
- `submission/backtest_report.md`

These numbers are sample paper-trading outputs, not investment advice and not a guarantee of future performance.

## Architecture

```text
LIST.md
  -> utils/data_loader.py
  -> Bitget symbol resolution and candles
  -> factors/*
  -> utils/scoring.py
  -> llm/deepseek_fusion.py
  -> trading/paper_trader.py
  -> trading/logger.py
  -> dashboard/app.py
```

Main modules:

- `main.py`: CLI entrypoint and end-to-end pipeline.
- `utils/market_data.py`: Bitget market data client, symbol mapping, candle download, and cache handling.
- `factors/`: technical, momentum, macro/sentiment placeholder, and category-leader factors.
- `llm/deepseek_fusion.py`: OpenAI-compatible DeepSeek call and JSON parsing fallback.
- `trading/paper_trader.py`: paper backtest, rebalancing, stop loss, fees, slippage, and performance metrics.
- `dashboard/app.py`: Gradio dashboard.

## Setup

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` locally. Do not commit `.env`.

```bash
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

DATA_SOURCE=bitget
YFINANCE_FALLBACK=false
INITIAL_CASH=10000
TOP_N=5
MAX_POSITION_PCT=0.20
STOP_LOSS_PCT=-0.05
FEE_BPS=10
SLIPPAGE_BPS=5

BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSPHRASE=
BITGET_BASE_URL=https://api.bitget.com
BITGET_ENABLED=true
BITGET_STOCK_SYMBOL_SUFFIX=ONUSDT
```

Bitget public market endpoints are used for the current data workflow. API key fields are kept for authenticated extensions and future account-aware features.
Environment variables set in the shell override values from `.env`.

## CLI Usage

Parse the universe:

```bash
python3 main.py parse-universe
```

Check Bitget symbol coverage:

```bash
python3 main.py check-symbols
```

Run a default signal and paper-trading cycle:

```bash
python3 main.py run --limit 24 --history-days 120 --backtest-days 30
```

Run a three-month backtest:

```bash
python3 main.py run --limit 24 --preset 3m
```

Run a six-month backtest:

```bash
python3 main.py run --limit 24 --preset 6m
```

Run without DeepSeek:

```bash
python3 main.py run --limit 24 --no-llm
```

## Dashboard Usage

Start locally:

```bash
python3 app.py
```

Open:

```text
http://127.0.0.1:7860
```

The dashboard includes:

- `Overview`: ranking table and factor contribution chart.
- `Trading`: paper-trading PnL, performance summary, recent trades, and CSV download.
- `Coverage`: skipped tickers and Bitget data errors.

Temporary public preview:

```bash
GRADIO_SHARE=true python3 app.py
```

For a stable public URL, deploy to Hugging Face Spaces, Render, or Railway and store `.env` values in the platform secret manager.

## Tests

```bash
python3 -m pytest -q
python3 -m compileall main.py utils trading dashboard app.py tests
```

The current test suite covers list parsing, factor calculations, backtest generation, costs, and backtest presets.

## Submission Readiness

The codebase is a working MVP for Bitget Hackathon Track 3:

- It uses Bitget as the default market data source.
- It produces a functioning AI-assisted stock signal workflow.
- It includes a paper-trading/backtest trail with fees, slippage, trades, equity, and performance metrics.
- It provides a dashboard and reproducible local commands.
- It includes sample outputs for judges to inspect.

Remaining external submission tasks:

- Create the public GitHub repository.
- Push this code to the repository.
- Deploy the Gradio dashboard to a public URL.
- Record a short demo video.
- Publish the required X post.
- Fill the official submission form.
- Add final links to `submission/SUBMISSION.md`.

## Limitations

- This is not a real-money trading bot.
- Unsupported Bitget stock-token symbols are skipped by default.
- Macro and sentiment factors are neutral placeholders in the MVP.
- The backtest is a lightweight daily-rebalance simulation, not a full institutional event-driven engine.
- Results depend on Bitget symbol availability and historical candle coverage.

## Submission Repository

GitHub repository used for submission:

```text
SignalCat
```
