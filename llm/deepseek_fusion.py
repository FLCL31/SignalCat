from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd
import requests

from utils.config import AppConfig


def annotate_with_deepseek(
    rankings: pd.DataFrame,
    config: AppConfig,
    max_items: int = 10,
    enabled: bool = True,
) -> tuple[pd.DataFrame, str]:
    if rankings.empty:
        return rankings, "No rankings available."
    if not enabled or not config.deepseek_api_key:
        return rankings, "DeepSeek disabled or API key missing; using deterministic reasons."

    subset = rankings.head(max_items).copy()
    prompt = _build_prompt(subset)
    payload = {
        "model": config.deepseek_model,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise quant analyst. Return strict JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }
    try:
        response = requests.post(
            f"{config.deepseek_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]
        content = message.get("content", "") or message.get("reasoning_content", "")
        if not content.strip():
            raise ValueError("DeepSeek returned empty content")
        parsed = _parse_json(content)
        return _merge_llm_output(rankings, parsed), str(parsed.get("overall_thesis", ""))
    except Exception as exc:
        return rankings, f"DeepSeek fallback used: {exc}"


def _build_prompt(frame: pd.DataFrame) -> str:
    records: list[dict[str, Any]] = []
    cols = [
        "ticker",
        "category",
        "symbol",
        "source",
        "price",
        "score",
        "technical_score",
        "momentum_score",
        "category_leader_score",
        "return_5d",
        "return_20d",
        "volatility_20d",
    ]
    for row in frame[cols].to_dict("records"):
        records.append({key: _round(value) for key, value in row.items()})
    return f"""
Analyze this AI stock-chain ranking table. Keep the quantitative ordering. Return reasons for exactly these tickers only.

Input rankings:
{json.dumps(records, ensure_ascii=False)}

Return strict JSON only:
{{
  "rankings": [
    {{"ticker": "NVDA", "score": 92, "reason": "50 Chinese characters or fewer"}}
  ],
  "overall_thesis": "One concise Chinese paragraph."
}}

Do not include markdown, comments, duplicate JSON objects, or text outside the JSON object.
"""


def _round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    return value


def _parse_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content).strip()
        content = re.sub(r"```$", "", content).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        try:
            parsed, _ = decoder.raw_decode(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", content, flags=re.S)
        if not match:
            raise
        snippet = match.group(0)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            parsed, _ = decoder.raw_decode(snippet)
            if isinstance(parsed, dict):
                return parsed
            raise


def _merge_llm_output(rankings: pd.DataFrame, parsed: dict[str, Any]) -> pd.DataFrame:
    output = rankings.copy()
    updates = {}
    for item in parsed.get("rankings", []):
        ticker = str(item.get("ticker", "")).upper()
        if not ticker:
            continue
        updates[ticker] = {
            "llm_score": item.get("score"),
            "llm_reason": item.get("reason"),
        }
    if not updates:
        return output
    output["llm_score"] = output["ticker"].map(lambda ticker: updates.get(ticker, {}).get("llm_score"))
    output["llm_reason"] = output["ticker"].map(lambda ticker: updates.get(ticker, {}).get("llm_reason"))
    output["reason"] = output["llm_reason"].where(output["llm_reason"].notna() & (output["llm_reason"] != ""), output["reason"])
    return output.drop(columns=["llm_reason"])
