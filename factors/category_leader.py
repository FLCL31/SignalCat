from __future__ import annotations

import pandas as pd


def add_category_leader_score(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if output.empty:
        output["category_leader_score"] = []
        return output
    output["category_leader_score"] = (
        output.groupby("category")["momentum_raw"]
        .rank(method="average", pct=True)
        .fillna(0.5)
        * 100.0
    )
    return output
