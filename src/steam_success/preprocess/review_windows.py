from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from steam_success.config import ProjectPaths, SETTINGS
from steam_success.preprocess.candidate_filter import parse_release_date


WINDOW_DAYS = (7, 30, 90)


def _truthy(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def _bucket_date(value: object) -> pd.Timestamp | pd.NaT:
    try:
        unix_value = int(str(value))
    except (TypeError, ValueError):
        return pd.NaT
    if unix_value <= 0:
        return pd.NaT
    return pd.Timestamp(datetime.fromtimestamp(unix_value, tz=timezone.utc).date())


def _positive_rate(up: int, total: int) -> float:
    return up / total if total else 0.0


def build_review_windows(candidates: pd.DataFrame, histogram: pd.DataFrame) -> pd.DataFrame:
    base = candidates.copy()
    if "release_date" not in base.columns:
        base["release_date"] = base["release_date_text"].map(parse_release_date)
    base["release_date"] = pd.to_datetime(base["release_date"], errors="coerce")
    base["label_eligible_90d"] = _truthy(base["label_eligible_90d"]) if "label_eligible_90d" in base.columns else False

    hist = histogram.copy()
    if hist.empty:
        for days in WINDOW_DAYS:
            base[f"reviews_{days}d"] = 0
            base[f"positive_reviews_{days}d"] = 0
            base[f"negative_reviews_{days}d"] = 0
            base[f"positive_rate_{days}d"] = 0.0
        base["success_90d"] = False
        return base

    hist["bucket_date"] = hist["bucket_date_unix"].map(_bucket_date)
    numeric_columns = ["recommendations_up", "recommendations_down", "recommendations_total"]
    for column in numeric_columns:
        hist[column] = pd.to_numeric(hist[column], errors="coerce").fillna(0).astype(int)

    merged = hist.merge(base[["appid", "release_date"]], on="appid", how="inner")
    merged = merged.dropna(subset=["release_date", "bucket_date"])
    merged["days_since_release"] = (merged["bucket_date"] - merged["release_date"]).dt.days

    for days in WINDOW_DAYS:
        in_window = merged[(merged["days_since_release"] >= 0) & (merged["days_since_release"] <= days)]
        grouped = (
            in_window.groupby("appid", as_index=False)[["recommendations_up", "recommendations_down", "recommendations_total"]]
            .sum()
            .rename(
                columns={
                    "recommendations_up": f"positive_reviews_{days}d",
                    "recommendations_down": f"negative_reviews_{days}d",
                    "recommendations_total": f"reviews_{days}d",
                }
            )
        )
        base = base.merge(grouped, on="appid", how="left")
        for column in (f"positive_reviews_{days}d", f"negative_reviews_{days}d", f"reviews_{days}d"):
            base[column] = pd.to_numeric(base[column], errors="coerce").fillna(0).astype(int)
        base[f"positive_rate_{days}d"] = [
            _positive_rate(up, total)
            for up, total in zip(base[f"positive_reviews_{days}d"], base[f"reviews_{days}d"], strict=False)
        ]

    base["success_90d"] = (
        base["label_eligible_90d"]
        & (base["reviews_90d"] >= SETTINGS.success_review_threshold)
        & (base["positive_rate_90d"] >= SETTINGS.success_positive_rate_threshold)
    )
    return base


def run(root: Path, candidates_csv: Path | None, histogram_csv: Path | None, output_name: str) -> Path:
    paths = ProjectPaths.from_root(root)
    resolved_candidates = candidates_csv if candidates_csv is not None else paths.data_interim / "game_candidates_2025_2026.csv"
    resolved_histogram = histogram_csv if histogram_csv is not None else paths.data_raw / "steam_review_histogram.csv"
    candidates = pd.read_csv(resolved_candidates)
    if not resolved_histogram.exists():
        raise FileNotFoundError(f"Histogram CSV not found: {resolved_histogram}")
    histogram = pd.read_csv(resolved_histogram)
    windows = build_review_windows(candidates, histogram)
    output = paths.data_interim / output_name
    windows.to_csv(output, index=False)
    print(f"candidate_rows={len(candidates)}")
    print(f"histogram_rows={len(histogram)}")
    print(f"output_rows={len(windows)}")
    print(f"label_eligible_90d_rows={int(windows['label_eligible_90d'].sum()) if 'label_eligible_90d' in windows.columns else 0}")
    print(f"success_90d_rows={int(windows['success_90d'].sum()) if 'success_90d' in windows.columns else 0}")
    print(f"output={output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build 7/30/90 day review metrics from Steam review histogram rollups.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--candidates-csv", type=Path, default=None)
    parser.add_argument("--histogram-csv", type=Path, default=None)
    parser.add_argument("--output", default="game_review_windows_2025_2026.csv")
    args = parser.parse_args()
    run(args.root.resolve(), args.candidates_csv, args.histogram_csv, args.output)


if __name__ == "__main__":
    main()
