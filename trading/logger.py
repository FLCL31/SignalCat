from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


TRADE_COLUMNS = [
    "timestamp",
    "ticker",
    "symbol",
    "direction",
    "price",
    "quantity",
    "balance_change",
    "reason",
]


def init_db(path: str | Path = "data/trades.db", reset: bool = False) -> Path:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if reset and db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ticker TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                balance_change REAL NOT NULL,
                reason TEXT NOT NULL
            )
            """
        )
    return db_path


def write_trades(trades: pd.DataFrame, db_path: str | Path = "data/trades.db", reset: bool = False) -> None:
    init_db(db_path, reset=reset)
    if trades.empty:
        return
    clean = trades[TRADE_COLUMNS].copy()
    clean["timestamp"] = clean["timestamp"].astype(str)
    with sqlite3.connect(db_path) as conn:
        clean.to_sql("trades", conn, if_exists="append", index=False)


def load_trades(db_path: str | Path = "data/trades.db") -> pd.DataFrame:
    path = Path(db_path)
    if not path.exists():
        return pd.DataFrame(columns=TRADE_COLUMNS)
    with sqlite3.connect(path) as conn:
        return pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp, id", conn)


def export_trades_csv(db_path: str | Path = "data/trades.db", csv_path: str | Path = "logs/trades.csv") -> Path:
    output = Path(csv_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    trades = load_trades(db_path)
    if "id" in trades.columns:
        trades = trades.drop(columns=["id"])
    trades.to_csv(output, index=False)
    return output
