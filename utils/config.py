from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path | None = None) -> dict[str, str]:
    env_path = path or ROOT / ".env"
    values: dict[str, str] = {}
    if env_path.exists():
        for raw_line in env_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    values.update(os.environ)
    return values


def _float(values: dict[str, str], key: str, default: float) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return default


def _int(values: dict[str, str], key: str, default: int) -> int:
    try:
        return int(float(values.get(key, default)))
    except (TypeError, ValueError):
        return default


def _bool(values: dict[str, str], key: str, default: bool) -> bool:
    value = values.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class AppConfig:
    root: Path
    data_source: str
    yfinance_fallback: bool
    initial_cash: float
    top_n: int
    max_position_pct: float
    stop_loss_pct: float
    fee_bps: float
    slippage_bps: float
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    bitget_api_key: str
    bitget_api_secret: str
    bitget_api_passphrase: str
    bitget_base_url: str
    bitget_enabled: bool
    bitget_stock_symbol_suffix: str

    @classmethod
    def from_env(cls, path: Path | None = None) -> "AppConfig":
        values = load_env(path)
        return cls(
            root=ROOT,
            data_source=values.get("DATA_SOURCE", "bitget").lower(),
            yfinance_fallback=_bool(values, "YFINANCE_FALLBACK", False),
            initial_cash=_float(values, "INITIAL_CASH", 10000.0),
            top_n=_int(values, "TOP_N", 5),
            max_position_pct=_float(values, "MAX_POSITION_PCT", 0.20),
            stop_loss_pct=_float(values, "STOP_LOSS_PCT", -0.05),
            fee_bps=_float(values, "FEE_BPS", 10.0),
            slippage_bps=_float(values, "SLIPPAGE_BPS", 5.0),
            deepseek_api_key=values.get("DEEPSEEK_API_KEY", ""),
            deepseek_base_url=values.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/"),
            deepseek_model=values.get("DEEPSEEK_MODEL", "deepseek-chat"),
            bitget_api_key=values.get("BITGET_API_KEY", ""),
            bitget_api_secret=values.get("BITGET_API_SECRET", ""),
            bitget_api_passphrase=values.get("BITGET_API_PASSPHRASE", ""),
            bitget_base_url=values.get("BITGET_BASE_URL", "https://api.bitget.com").rstrip("/"),
            bitget_enabled=_bool(values, "BITGET_ENABLED", True),
            bitget_stock_symbol_suffix=values.get("BITGET_STOCK_SYMBOL_SUFFIX", "ONUSDT"),
        )

    @property
    def use_bitget(self) -> bool:
        return self.data_source == "bitget" and self.bitget_enabled
