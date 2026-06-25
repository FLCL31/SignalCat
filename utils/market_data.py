from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

from utils.config import AppConfig


class MarketDataError(RuntimeError):
    pass


@dataclass
class HistoryResult:
    histories: dict[str, pd.DataFrame]
    symbol_map: dict[str, str]
    source_map: dict[str, str]
    errors: dict[str, str]


class MarketDataClient:
    def __init__(self, config: AppConfig, cache_dir: str | Path = "data/prices") -> None:
        self.config = config
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self._bitget_symbols: set[str] | None = None

    def fetch_histories(self, tickers: list[str], days: int = 120) -> HistoryResult:
        histories: dict[str, pd.DataFrame] = {}
        symbol_map: dict[str, str] = {}
        source_map: dict[str, str] = {}
        errors: dict[str, str] = {}

        for ticker in tickers:
            ticker = ticker.upper()
            try:
                history, symbol, source = self.fetch_history(ticker, days=days)
                if history.empty:
                    raise MarketDataError("empty history")
                histories[ticker] = history
                symbol_map[ticker] = symbol
                source_map[ticker] = source
                self._write_cache(ticker, history)
            except Exception as exc:
                if self.config.use_bitget and not self.config.yfinance_fallback and "No Bitget spot symbol found" in str(exc):
                    errors[ticker] = str(exc)
                    continue
                cached = self._read_cache(ticker)
                if cached is not None and not cached.empty:
                    histories[ticker] = cached
                    symbol_map[ticker] = ticker
                    source_map[ticker] = "cache"
                    errors[ticker] = f"using cache after error: {exc}"
                else:
                    errors[ticker] = str(exc)
        return HistoryResult(histories=histories, symbol_map=symbol_map, source_map=source_map, errors=errors)

    def fetch_history(self, ticker: str, days: int = 120) -> tuple[pd.DataFrame, str, str]:
        if self.config.use_bitget:
            try:
                symbol = self.resolve_bitget_symbol(ticker)
                history = self.fetch_bitget_candles(symbol, days=days)
                if not history.empty:
                    return history, symbol, "bitget"
            except Exception as exc:
                bitget_error = exc
            else:
                bitget_error = MarketDataError("bitget returned empty history")
        else:
            bitget_error = MarketDataError("bitget disabled")

        if not self.config.yfinance_fallback and self.config.data_source != "yfinance":
            raise MarketDataError(f"bitget failed and yfinance fallback is disabled: {bitget_error}")

        try:
            history = self.fetch_yfinance_history(ticker, days=days)
            if not history.empty:
                return history, ticker, "yfinance"
        except Exception as exc:
            raise MarketDataError(f"bitget failed: {bitget_error}; yfinance failed: {exc}") from exc
        raise MarketDataError(f"bitget failed: {bitget_error}; yfinance returned empty history")

    def get_bitget_symbols(self) -> set[str]:
        if self._bitget_symbols is not None:
            return self._bitget_symbols
        url = f"{self.config.bitget_base_url}/api/v2/spot/public/symbols"
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != "00000":
            raise MarketDataError(f"Bitget symbols error: {payload.get('msg')}")
        symbols = set()
        for item in payload.get("data") or []:
            symbol = str(item.get("symbol", "")).upper()
            if symbol:
                symbols.add(symbol)
        self._bitget_symbols = symbols
        return symbols

    def resolve_bitget_symbol(self, ticker: str) -> str:
        symbols = self.get_bitget_symbols()
        suffix = self.config.bitget_stock_symbol_suffix.upper()
        candidates = [
            f"{ticker}{suffix}",
            f"R{ticker}USDT",
            f"{ticker}USDT",
        ]
        for candidate in candidates:
            if candidate.upper() in symbols:
                return candidate.upper()
        raise MarketDataError(f"No Bitget spot symbol found for {ticker}; tried {candidates}")

    def fetch_bitget_ticker(self, symbol: str) -> dict[str, object]:
        url = f"{self.config.bitget_base_url}/api/v2/spot/market/tickers"
        response = self.session.get(url, params={"symbol": symbol}, timeout=20)
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != "00000":
            raise MarketDataError(f"Bitget ticker error for {symbol}: {payload.get('msg')}")
        data = payload.get("data") or []
        if not data:
            raise MarketDataError(f"No Bitget ticker data for {symbol}")
        return data[0]

    def fetch_bitget_candles(self, symbol: str, days: int = 120) -> pd.DataFrame:
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - int(days * 24 * 60 * 60 * 1000)
        params = {
            "symbol": symbol,
            "granularity": "1day",
            "startTime": str(start_ms),
            "endTime": str(end_ms),
            "limit": str(min(max(days, 30), 200)),
        }
        errors: list[str] = []
        for path in ("/api/v2/spot/market/candles", "/api/v2/spot/market/history-candles"):
            url = f"{self.config.bitget_base_url}{path}"
            response = self.session.get(url, params=params, timeout=20)
            if response.status_code >= 400:
                errors.append(f"{path}: http {response.status_code}")
                continue
            payload = response.json()
            if payload.get("code") != "00000":
                errors.append(f"{path}: {payload.get('msg')}")
                continue
            frame = self._candles_to_frame(payload.get("data") or [])
            if not frame.empty:
                return frame
        raise MarketDataError(f"No Bitget candle data for {symbol}: {'; '.join(errors)}")

    def fetch_yfinance_history(self, ticker: str, days: int = 120) -> pd.DataFrame:
        import yfinance as yf

        frame = yf.download(
            ticker,
            period=f"{max(days, 30)}d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if frame.empty:
            return frame
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = [col[0] for col in frame.columns]
        frame = frame.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        frame = frame[["open", "high", "low", "close", "volume"]].copy()
        frame.index = pd.to_datetime(frame.index)
        frame.index.name = "timestamp"
        return frame.dropna(subset=["close"]).sort_index()

    def _candles_to_frame(self, rows: list[list[str]]) -> pd.DataFrame:
        parsed: list[dict[str, float | pd.Timestamp]] = []
        for row in rows:
            if len(row) < 6:
                continue
            parsed.append(
                {
                    "timestamp": pd.to_datetime(int(row[0]), unit="ms", utc=True).tz_convert(None),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5]),
                }
            )
        if not parsed:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        frame = pd.DataFrame(parsed).drop_duplicates(subset=["timestamp"])
        frame = frame.set_index("timestamp").sort_index()
        return frame[["open", "high", "low", "close", "volume"]]

    def _cache_path(self, ticker: str) -> Path:
        return self.cache_dir / f"{ticker.upper()}.csv"

    def _write_cache(self, ticker: str, history: pd.DataFrame) -> None:
        path = self._cache_path(ticker)
        history.to_csv(path)

    def _read_cache(self, ticker: str) -> pd.DataFrame | None:
        path = self._cache_path(ticker)
        if not path.exists():
            return None
        frame = pd.read_csv(path, parse_dates=["timestamp"], index_col="timestamp")
        return frame.sort_index()
