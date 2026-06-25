# AI Hybrid Signal Engine

AI Hybrid Signal Engine turns a TradingView AI stock-chain watchlist into a dynamic ranking and paper-trading system for the Bitget AI Hackathon Track 3.

The current universe is `211` US-listed AI infrastructure and application stocks across `24` categories. The MVP uses Bitget spot market data, maps tickers such as `NVDA -> NVDAONUSDT`, and skips unsupported tickers by default. Trading is paper-only.

## What It Does

- Parses `LIST.md` into a structured stock universe.
- Fetches Bitget stock-token market data and caches price histories.
- Computes technical, momentum, category-leader, macro, and sentiment scores.
- Uses DeepSeek to refine concise ranking reasons when configured.
- Runs a simple paper-trading backtest and writes SQLite + CSV logs.
- Serves a Gradio dashboard with rankings, factor contribution, PnL, and trades.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with DeepSeek and Bitget credentials. Do not commit `.env`.

## Run

Parse the universe:

```bash
python main.py parse-universe
```

Run the MVP pipeline:

```bash
python main.py run --limit 24 --history-days 120 --backtest-days 30
```

Check Bitget symbol coverage for the full watchlist:

```bash
python main.py check-symbols
```

Run without DeepSeek:

```bash
python main.py run --limit 24 --no-llm
```

Start the dashboard:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:7860
```

Temporary public preview without a deployment account:

```bash
GRADIO_SHARE=true python app.py
```

## Outputs

- `data/universe.csv`
- `data/latest_rankings.csv`
- `data/equity_curve.csv`
- `data/data_errors.csv`
- `data/bitget_symbol_coverage.csv`
- `data/trades.db`
- `logs/trades.csv`

## Deployment

Hugging Face Spaces:

- Create a new Gradio Space.
- Upload this repository.
- Add `.env` values as Space secrets.
- The root `app.py` is the entrypoint.

Railway / Render:

- Use `Procfile` or `render.yaml`.
- Set the same environment variables from `.env` in the platform secret manager.
- Do not upload `.env`.

## Notes

- The default route is Bitget-only. Set `YFINANCE_FALLBACK=true` only if you explicitly want public-market fallback data.
- Real orders are not implemented. All trading is simulated.
- `logs/trades.csv` is included as a sample paper-trading log and can be regenerated.
