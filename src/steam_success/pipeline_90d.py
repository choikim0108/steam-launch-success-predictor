from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import cast

import pandas as pd

from steam_success.config import ProjectPaths, SETTINGS
from steam_success.features.build_features import FEATURE_COLUMNS
from steam_success.market_report import write_market_insight_site
from steam_success.models.train import train_and_evaluate
from steam_success.preprocess.dataset import _contains, _count_languages
from steam_success.reporting import build_criteria_tables, write_run_summary
from steam_success.web_report import write_interactive_report
from steam_success.visualize.charts import make_charts


TRUTHY = {"true", "1", "yes"}


def _truthy_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin(TRUTHY)


def _series(data: pd.DataFrame, column: str, default: object) -> pd.Series:
    if column in data.columns:
        return cast(pd.Series, data[column])
    return pd.Series(default, index=data.index)


def _numeric_series(series: pd.Series, default: float = 0.0) -> pd.Series:
    return cast(pd.Series, pd.to_numeric(series, errors="coerce")).fillna(default)


def _load_release_window_count(paths: ProjectPaths, release_window_csv: Path | None) -> int:
    path = release_window_csv if release_window_csv is not None else paths.data_interim / "search_release_window_appids.csv"
    if not path.exists():
        return 0
    return int(len(pd.read_csv(path)))


def build_90d_modeling_dataset(windows: pd.DataFrame, release_window_candidate_count: int) -> pd.DataFrame:
    if "label_eligible_90d" not in windows.columns:
        raise ValueError("90d windows data must include label_eligible_90d.")
    data = cast(pd.DataFrame, windows[_truthy_series(_series(windows, "label_eligible_90d", False))].copy())
    if data.empty:
        raise RuntimeError("No label-eligible 90d rows available.")
    data["success"] = _truthy_series(_series(data, "success_90d", False)).astype(int)
    data["total_reviews"] = _numeric_series(_series(data, "reviews_90d", 0), 0).astype(int)
    data["positive_rate"] = _numeric_series(_series(data, "positive_rate_90d", 0.0), 0.0).astype(float)
    data["review_count_30d"] = _numeric_series(_series(data, "reviews_30d", 0), 0).astype(int)
    data["review_count_90d"] = _series(data, "total_reviews", 0)
    data["price_final_usd"] = _numeric_series(_series(data, "price_final_usd", 0), 0.0).astype(float)
    data["is_free"] = _truthy_series(_series(data, "is_free", False))
    data["coming_soon"] = _truthy_series(_series(data, "coming_soon", False))
    data["required_age"] = _numeric_series(_series(data, "required_age", 0), 0).astype(int)
    data["discount_percent"] = _numeric_series(_series(data, "discount_percent", 0), 0).astype(float)
    data["supported_language_count"] = _series(data, "supported_languages_raw", "").map(_count_languages)
    data["genre_count"] = _series(data, "genres", "").fillna("").map(lambda value: len([part for part in str(value).split(",") if part.strip()]))
    data["category_count"] = _series(data, "categories", "").fillna("").map(lambda value: len([part for part in str(value).split(",") if part.strip()]))
    categories = _series(data, "categories", "")
    data["has_multiplayer"] = categories.map(lambda value: _contains(value, "Multi-player") or _contains(value, "Co-op"))
    data["has_singleplayer"] = categories.map(lambda value: _contains(value, "Single-player"))
    data["supports_achievements"] = categories.map(lambda value: _contains(value, "Achievements"))
    data["supports_controller"] = categories.map(lambda value: _contains(value, "Controller"))
    for column in ["platform_windows", "platform_mac", "platform_linux"]:
        data[column] = _truthy_series(_series(data, column, False))
    for column in ["youtube_mentions", "webzine_mentions", "blog_mentions", "external_attention_score"]:
        if column not in data.columns:
            data[column] = 0
    data["release_window_candidate_count"] = release_window_candidate_count
    missing = [column for column in FEATURE_COLUMNS if column not in data.columns]
    if missing:
        raise RuntimeError(f"Missing feature columns: {missing}")
    return data.reset_index(drop=True)


def run(root: Path, windows_csv: Path | None = None, release_window_csv: Path | None = None) -> Path:
    paths = ProjectPaths.from_root(root)
    resolved_windows = windows_csv if windows_csv is not None else paths.data_interim / "game_review_windows_2025_2026.csv"
    windows = pd.read_csv(resolved_windows)
    release_window_count = _load_release_window_count(paths, release_window_csv)
    dataset = build_90d_modeling_dataset(windows, release_window_count)
    reports_dir = paths.reports / "90d"
    figures_dir = reports_dir / "figures"
    models_dir = paths.models / "90d"
    reports_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(paths.data_processed / "modeling_dataset_90d.csv", index=False)
    result = train_and_evaluate(dataset, models_dir, reports_dir, SETTINGS)
    model_output = models_dir / "steam_success_model.joblib"
    if model_output.exists():
        shutil.copy2(model_output, paths.models / "steam_success_90d_model.joblib")
    for name, table in build_criteria_tables(dataset).items():
        table.to_csv(reports_dir / f"criteria_{name}.csv", index=False)
    predictions = pd.read_csv(reports_dir / "predictions.csv")
    dataset = dataset.merge(predictions[["appid", "predicted_success_probability"]], on="appid", how="left")
    feature_importance = pd.read_csv(reports_dir / "feature_importance.csv")
    chart_paths = make_charts(dataset, feature_importance, figures_dir, {"summary": []})
    write_run_summary(reports_dir, dataset, result, chart_paths)
    write_interactive_report(reports_dir, dataset)
    write_market_insight_site(reports_dir, dataset, pd.DataFrame(), feature_importance)
    print("Steam 90d success prediction pipeline completed")
    success_count = int(_numeric_series(_series(dataset, "success", 0), 0).sum())
    print(f"valid_games={len(dataset)} success_90d={success_count}")
    print(f"reports={reports_dir}")
    return reports_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and regenerate reports from 90-day Steam review window data.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--windows-csv", type=Path, default=None)
    parser.add_argument("--release-window-csv", type=Path, default=None)
    args = parser.parse_args()
    run(args.root.resolve(), args.windows_csv, args.release_window_csv)


if __name__ == "__main__":
    main()
