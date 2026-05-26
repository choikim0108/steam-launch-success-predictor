from __future__ import annotations

import re

import pandas as pd

from steam_success.config import ProjectSettings, SETTINGS


def _count_languages(value: object) -> int:
    if not isinstance(value, str) or not value.strip():
        return 0
    cleaned = re.sub(r"<[^>]+>", ",", value)
    cleaned = cleaned.replace("*", "")
    parts = [p.strip() for p in re.split(r",|\n|;", cleaned) if p.strip()]
    return len(set(parts))


def _contains(text: object, needle: str) -> bool:
    return isinstance(text, str) and needle.lower() in text.lower()


def build_modeling_dataset(search: pd.DataFrame, details: pd.DataFrame, reviews: pd.DataFrame, settings: ProjectSettings = SETTINGS) -> pd.DataFrame:
    data = search.merge(details, on="appid", how="left").merge(reviews, on="appid", how="left")
    data = data[(data["detail_success"] == True) & (data["type"] == "game") & (data["coming_soon"] == False)].copy()
    data["total_reviews"] = data["total_reviews"].fillna(0).astype(int)
    data["positive_rate"] = data["positive_rate"].fillna(0.0).astype(float)
    data["recommendations_total"] = data["recommendations_total"].fillna(0).astype(int)
    data["metacritic_score"] = data["metacritic_score"].fillna(0).astype(float)
    data["price_final_usd"] = data["price_final_usd"].fillna(0.0).astype(float)
    data["is_free"] = data["is_free"].fillna(False).astype(bool)
    data["supported_language_count"] = data["supported_languages_raw"].map(_count_languages)
    data["genre_count"] = data["genres"].fillna("").map(lambda x: len([p for p in str(x).split(",") if p.strip()]))
    data["category_count"] = data["categories"].fillna("").map(lambda x: len([p for p in str(x).split(",") if p.strip()]))
    data["has_multiplayer"] = data["categories"].map(lambda x: _contains(x, "Multi-player") or _contains(x, "Co-op"))
    data["has_singleplayer"] = data["categories"].map(lambda x: _contains(x, "Single-player"))
    data["supports_achievements"] = data["categories"].map(lambda x: _contains(x, "Achievements"))
    data["supports_controller"] = data["categories"].map(lambda x: _contains(x, "Controller"))
    data["success"] = (
        (data["total_reviews"] >= settings.success_review_threshold)
        & (data["positive_rate"] >= settings.success_positive_rate_threshold)
    ).astype(int)
    return data.sort_values(["success", "total_reviews"], ascending=[False, False]).reset_index(drop=True)
