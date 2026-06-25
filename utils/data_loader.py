from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_universe(path: str | Path = "LIST.md") -> pd.DataFrame:
    source = Path(path)
    rows: list[dict[str, object]] = []
    for raw_line in source.read_text().splitlines():
        parts = raw_line.strip().split("\t")
        if len(parts) != 4 or not parts[0].isdigit():
            continue
        rows.append(
            {
                "index": int(parts[0]),
                "category": parts[1].strip(),
                "ticker": parts[2].strip().upper(),
                "exchange": parts[3].strip().upper(),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError(f"No stock rows parsed from {source}")
    if df["ticker"].duplicated().any():
        dupes = sorted(df.loc[df["ticker"].duplicated(), "ticker"].unique())
        raise ValueError(f"Duplicate tickers in universe: {dupes}")
    return df


def select_representative_universe(universe: pd.DataFrame, limit: int | None) -> pd.DataFrame:
    if not limit or limit <= 0 or limit >= len(universe):
        return universe.copy().reset_index(drop=True)
    buckets = {category: group.copy() for category, group in universe.groupby("category", sort=False)}
    selected: list[pd.Series] = []
    while len(selected) < limit and buckets:
        for category in list(buckets.keys()):
            group = buckets[category]
            if group.empty:
                buckets.pop(category, None)
                continue
            selected.append(group.iloc[0])
            buckets[category] = group.iloc[1:]
            if len(selected) >= limit:
                break
    return pd.DataFrame(selected).reset_index(drop=True)


def write_universe_csv(universe: pd.DataFrame, path: str | Path = "data/universe.csv") -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    universe.to_csv(output, index=False)
    return output
