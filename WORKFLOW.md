# Project Workflow

## User Flow

1. Configure `.env` with DeepSeek and Bitget credentials.
2. Check the watchlist:

```bash
python3 main.py parse-universe
```

3. Check Bitget symbol coverage:

```bash
python3 main.py check-symbols
```

4. Run a signal cycle:

```bash
python3 main.py run --limit 24 --history-days 120 --backtest-days 30
```

5. Open the dashboard:

```bash
python3 app.py
```

6. Review rankings, factor contribution, paper-trading PnL, recent trades, and skipped tickers.

## System Flow

```text
LIST.md
  -> parse universe
  -> map ticker to Bitget spot symbol
  -> fetch Bitget candles
  -> compute factors
  -> score and rank
  -> ask DeepSeek for concise rationale
  -> run paper-trading backtest
  -> write SQLite/CSV logs
  -> render Gradio dashboard
```

## Operating Modes

- Dashboard mode: use `python3 app.py` and click `Run Pipeline`.
- CLI mode: use `python3 main.py run ...` for scripted runs.
- Coverage mode: use `python3 main.py check-symbols` before expanding the universe.

## Three-Month Backtest

The current paper-trading engine supports a three-month window. Use:

```bash
python3 main.py run --limit 24 --preset 3m
```

The dashboard also allows `Backtest Days` up to `180` and includes `Custom`, `3 Months`, and `6 Months` presets.

Six-month mode:

```bash
python3 main.py run --limit 24 --preset 6m
```

The engine applies `FEE_BPS` and `SLIPPAGE_BPS` from `.env` to paper-trading executions.

## Deferred Interfaces

Telegram bot control is intentionally deferred. The current MVP focuses on the CLI, Gradio dashboard, Bitget market data, DeepSeek explanations, and reproducible paper-trading logs.
