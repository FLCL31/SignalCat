from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from llm.deepseek_fusion import annotate_with_deepseek
from trading.logger import export_trades_csv, write_trades
from trading.paper_trader import BacktestResult, run_backtest
from utils.config import AppConfig
from utils.data_loader import load_universe, select_representative_universe, write_universe_csv
from utils.market_data import HistoryResult, MarketDataClient
from utils.scoring import build_score_table


@dataclass
class PipelineResult:
    universe: pd.DataFrame
    rankings: pd.DataFrame
    history_result: HistoryResult
    backtest: BacktestResult
    thesis: str
    ranking_path: Path
    equity_path: Path
    errors_path: Path
    trades_csv_path: Path


def run_pipeline(
    limit: int = 24,
    history_days: int = 120,
    backtest_days: int = 30,
    use_llm: bool = True,
    reset_logs: bool = True,
) -> PipelineResult:
    config = AppConfig.from_env()
    universe_all = load_universe(config.root / "LIST.md")
    universe = select_representative_universe(universe_all, limit)
    write_universe_csv(universe_all, config.root / "data/universe.csv")

    client = MarketDataClient(config, cache_dir=config.root / "data/prices")
    history_result = client.fetch_histories(universe["ticker"].tolist(), days=history_days)
    rankings = build_score_table(universe, history_result.histories, history_result.symbol_map, history_result.source_map)
    rankings, thesis = annotate_with_deepseek(rankings, config, max_items=min(config.top_n, len(rankings)), enabled=use_llm)

    backtest = run_backtest(rankings, history_result.histories, config, days=backtest_days)

    ranking_path = config.root / "data/latest_rankings.csv"
    equity_path = config.root / "data/equity_curve.csv"
    errors_path = config.root / "data/data_errors.csv"
    ranking_path.parent.mkdir(parents=True, exist_ok=True)
    rankings.to_csv(ranking_path, index=False)
    backtest.equity_curve.to_csv(equity_path, index=False)
    _write_errors(history_result.errors, errors_path)
    write_trades(backtest.trades, config.root / "data/trades.db", reset=reset_logs)
    trades_csv_path = export_trades_csv(config.root / "data/trades.db", config.root / "logs/trades.csv")

    return PipelineResult(
        universe=universe,
        rankings=rankings,
        history_result=history_result,
        backtest=backtest,
        thesis=thesis,
        ranking_path=ranking_path,
        equity_path=equity_path,
        errors_path=errors_path,
        trades_csv_path=trades_csv_path,
    )


def _write_errors(errors: dict[str, str], path: Path) -> None:
    rows = [{"ticker": ticker, "error": error} for ticker, error in sorted(errors.items())]
    pd.DataFrame(rows, columns=["ticker", "error"]).to_csv(path, index=False)


def parse_universe() -> None:
    universe = load_universe("LIST.md")
    path = write_universe_csv(universe)
    print(f"rows={len(universe)}")
    print(f"unique_tickers={universe['ticker'].nunique()}")
    print(f"unique_categories={universe['category'].nunique()}")
    print(f"output={path}")


def check_symbols(limit: int = 0) -> None:
    config = AppConfig.from_env()
    universe = load_universe(config.root / "LIST.md")
    if limit and limit > 0:
        universe = universe.head(limit).copy()
    client = MarketDataClient(config, cache_dir=config.root / "data/prices")
    rows = []
    for item in universe.to_dict("records"):
        ticker = str(item["ticker"])
        try:
            symbol = client.resolve_bitget_symbol(ticker)
            status = "supported"
            error = ""
        except Exception as exc:
            symbol = ""
            status = "unsupported"
            error = str(exc)
        rows.append(
            {
                "ticker": ticker,
                "category": item["category"],
                "exchange": item["exchange"],
                "bitget_symbol": symbol,
                "status": status,
                "error": error,
            }
        )
    output = config.root / "data/bitget_symbol_coverage.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(output, index=False)
    print(f"coverage_rows={len(frame)}")
    print(f"supported={(frame['status'] == 'supported').sum()}")
    print(f"unsupported={(frame['status'] == 'unsupported').sum()}")
    print(f"output={output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Hybrid Signal Engine")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("parse-universe", help="Parse LIST.md and write data/universe.csv")
    coverage = sub.add_parser("check-symbols", help="Check Bitget symbol coverage for LIST.md")
    coverage.add_argument("--limit", type=int, default=0)

    run = sub.add_parser("run", help="Run signal generation and paper trading")
    run.add_argument("--limit", type=int, default=24, help="Ticker limit for MVP run; 0 means full universe")
    run.add_argument("--history-days", type=int, default=120)
    run.add_argument("--backtest-days", type=int, default=30)
    run.add_argument("--no-llm", action="store_true", help="Disable DeepSeek and use deterministic reasons")
    run.add_argument("--append-logs", action="store_true", help="Append to existing trade logs instead of resetting")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "parse-universe":
        parse_universe()
        return
    if args.command == "check-symbols":
        check_symbols(limit=args.limit)
        return
    if args.command in {None, "run"}:
        result = run_pipeline(
            limit=args.limit if hasattr(args, "limit") else 24,
            history_days=args.history_days if hasattr(args, "history_days") else 120,
            backtest_days=args.backtest_days if hasattr(args, "backtest_days") else 30,
            use_llm=not getattr(args, "no_llm", False),
            reset_logs=not getattr(args, "append_logs", False),
        )
        print(f"universe_rows={len(result.universe)}")
        print(f"rankings_rows={len(result.rankings)}")
        print(f"history_success={len(result.history_result.histories)}")
        print(f"history_errors={len(result.history_result.errors)}")
        print(f"trades_rows={len(result.backtest.trades)}")
        print(f"ranking_path={result.ranking_path}")
        print(f"equity_path={result.equity_path}")
        print(f"errors_path={result.errors_path}")
        print(f"trades_csv_path={result.trades_csv_path}")
        if result.thesis:
            print(f"thesis={result.thesis[:240]}")
        if result.history_result.errors:
            sample = list(result.history_result.errors.items())[:5]
            print(f"history_error_sample={sample}")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
