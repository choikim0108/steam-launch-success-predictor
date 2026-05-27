from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from steam_success.config import ProjectSettings, SETTINGS


def _records(data: pd.DataFrame) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], data.to_dict(orient="records"))


def _as_int(value: object) -> int:
    return int(float(str(value)))


def _as_float(value: object) -> float:
    return float(str(value))


def _split_values(value: object) -> list[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def high_success_genres(dataset: pd.DataFrame, limit: int = 3) -> list[str]:
    rows: list[dict[str, object]] = []
    source = cast(pd.DataFrame, dataset[["genres", "success", "predicted_success_probability"]])
    for record in _records(source):
        for genre in _split_values(record["genres"]):
            rows.append({"genre": genre, "success": _as_int(record["success"]), "probability": _as_float(record["predicted_success_probability"])})
    if not rows:
        return []
    summary = cast(pd.DataFrame, pd.DataFrame(rows).groupby("genre", as_index=False).agg(
        game_count=("success", "size"),
        success_count=("success", "sum"),
        average_probability=("probability", "mean"),
    ))
    summary["success_rate"] = summary["success_count"] / summary["game_count"]
    ranked_source = cast(pd.DataFrame, summary[summary["game_count"] >= 3])
    ranked = ranked_source.sort_values(by=["average_probability", "success_rate", "game_count"], ascending=False)
    return ranked.head(limit)["genre"].astype(str).tolist()


def select_review_games(dataset: pd.DataFrame, settings: ProjectSettings = SETTINGS) -> pd.DataFrame:
    genres = high_success_genres(dataset)
    rows: list[dict[str, object]] = []
    sorted_dataset = dataset.sort_values(by=["predicted_success_probability"], ascending=False)
    for record in _records(sorted_dataset):
        record_genres = _split_values(record["genres"])
        matched = [genre for genre in genres if genre in record_genres]
        if matched:
            rows.append({
                "appid": _as_int(record["appid"]),
                "name": str(record["name"]),
                "success": _as_int(record["success"]),
                "matched_genres": ", ".join(matched),
                "predicted_success_probability": _as_float(record["predicted_success_probability"]),
                "total_reviews": _as_int(record["total_reviews"]),
            })
    candidates = pd.DataFrame(rows)
    if candidates.empty:
        return candidates
    selected: list[pd.DataFrame] = []
    per_bucket = max(1, settings.review_text_sample_size // max(1, len(genres) * 2))
    for genre in genres:
        matched_genres = cast(pd.Series, candidates["matched_genres"])
        genre_rows = cast(pd.DataFrame, candidates[matched_genres.str.contains(genre, regex=False, na=False)])
        for success_value in [1, 0]:
            bucket_source = cast(pd.DataFrame, genre_rows[genre_rows["success"] == success_value])
            bucket = bucket_source.sort_values(by=["total_reviews", "predicted_success_probability"], ascending=False).head(per_bucket)
            selected.append(bucket)
    result = pd.concat(selected, ignore_index=True).drop_duplicates("appid") if selected else candidates.head(0)
    if len(result) < settings.review_text_sample_size:
        extra = candidates.sort_values(by=["total_reviews", "predicted_success_probability"], ascending=False).head(settings.review_text_sample_size)
        result = pd.concat([result, extra], ignore_index=True).drop_duplicates("appid")
    return result.head(settings.review_text_sample_size)


def _clean_text(text: object) -> str:
    value = re.sub(r"https?://\S+", " ", str(text).lower())
    value = re.sub(r"[^a-z0-9가-힣 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _keywords(texts: pd.Series) -> str:
    cleaned = [_clean_text(text) for text in texts if len(_clean_text(text)) >= 20]
    if not cleaned:
        return "데이터 부족"
    vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1, max_features=60)
    matrix = cast(Any, vectorizer.fit_transform(cleaned))
    scores = np.asarray(matrix.sum(axis=0)).ravel().tolist()
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(terms, scores, strict=False), key=lambda item: item[1], reverse=True)
    return ", ".join(term for term, _ in ranked[:8])


def analyze_review_topics(dataset: pd.DataFrame, reviews: pd.DataFrame, reports_dir: Path) -> dict[str, object]:
    if reviews.empty:
        empty = pd.DataFrame(columns=["genre", "game_success", "review_sentiment", "review_count", "top_terms"])
        empty.to_csv(reports_dir / "review_topic_summary.csv", index=False)
        return {"top_genres": high_success_genres(dataset), "summary": []}
    selected = select_review_games(dataset)
    merged = cast(pd.DataFrame, reviews.merge(selected, on="appid", how="inner"))
    review_text = cast(pd.Series, merged["review_text"])
    merged = cast(pd.DataFrame, merged[review_text.fillna("").str.len() > 0].copy())
    voted_up = cast(pd.Series, merged["voted_up"])
    merged["review_sentiment"] = voted_up.map(lambda value: "positive" if bool(value) else "negative")
    rows: list[dict[str, object]] = []
    for genre in high_success_genres(dataset):
        matched_genres = cast(pd.Series, merged["matched_genres"])
        genre_reviews = cast(pd.DataFrame, merged[matched_genres.str.contains(genre, regex=False, na=False)])
        for success_value, game_label in [(1, "success"), (0, "failure")]:
            game_reviews = genre_reviews[genre_reviews["success"] == success_value]
            for sentiment in ["positive", "negative"]:
                subset = cast(pd.DataFrame, game_reviews[game_reviews["review_sentiment"] == sentiment])
                rows.append({
                    "genre": genre,
                    "game_success": game_label,
                    "review_sentiment": sentiment,
                    "review_count": int(len(subset)),
                    "top_terms": _keywords(cast(pd.Series, subset["review_text"])),
                })
    summary = pd.DataFrame(rows)
    summary.to_csv(reports_dir / "review_topic_summary.csv", index=False)
    merged[["appid", "name", "matched_genres", "success", "voted_up", "playtime_hours", "review_text"]].to_csv(reports_dir / "review_samples.csv", index=False)
    return {"top_genres": high_success_genres(dataset), "summary": _records(summary)}
