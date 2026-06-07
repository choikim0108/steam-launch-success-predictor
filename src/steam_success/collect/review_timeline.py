from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from steam_success.collect.steam import CrawlConfig, fetch_review_timeline
from steam_success.config import ProjectPaths, SETTINGS


def _appid_list(input_csv: Path, max_apps: int | None, appids: list[int] | None) -> list[int]:
    if appids:
        values = appids
    else:
        if not input_csv.exists():
            raise FileNotFoundError(f"Input CSV not found: {input_csv}")
        data = pd.read_csv(input_csv)
        if "appid" not in data.columns:
            raise ValueError(f"Input CSV must contain an appid column: {input_csv}")
        values = data["appid"].dropna().astype(int).drop_duplicates().tolist()
    if max_apps is not None:
        values = values[:max_apps]
    if not values:
        raise ValueError("No appids to collect.")
    return values


def run(
    root: Path,
    input_csv: Path | None,
    appids: list[int] | None,
    max_apps: int | None,
    max_reviews_per_game: int,
    page_size: int,
) -> Path:
    paths = ProjectPaths.from_root(root)
    resolved_input = input_csv if input_csv is not None else paths.data_interim / "search_release_window_appids.csv"
    selected_appids = _appid_list(resolved_input, max_apps, appids)
    config = CrawlConfig(
        max_apps=len(selected_appids),
        pages=SETTINGS.search_pages,
        sleep_seconds=SETTINGS.request_sleep_seconds,
        country=SETTINGS.country,
        language=SETTINGS.language,
    )
    timeline = fetch_review_timeline(
        selected_appids,
        paths.data_raw,
        config,
        page_size=page_size,
        max_reviews_per_game=max_reviews_per_game,
    )
    output = paths.data_raw / "steam_review_timeline.csv"
    timeline.to_csv(output, index=False)
    print(f"review_timeline_rows={len(timeline)}")
    print(f"appids={len(selected_appids)}")
    print(f"output={output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Steam review pages with timestamps for 7/30/90 day metrics.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--input-csv", type=Path, default=None, help="CSV with an appid column. Defaults to data/interim/search_release_window_appids.csv")
    parser.add_argument("--appid", type=int, action="append", dest="appids", help="Collect one appid. Can be repeated.")
    parser.add_argument("--max-apps", type=int, default=None, help="Limit appids loaded from the input CSV.")
    parser.add_argument("--max-reviews-per-game", type=int, default=SETTINGS.review_timeline_max_reviews_per_game)
    parser.add_argument("--page-size", type=int, default=SETTINGS.review_timeline_page_size)
    args = parser.parse_args()
    run(
        args.root.resolve(),
        args.input_csv,
        args.appids,
        args.max_apps,
        args.max_reviews_per_game,
        args.page_size,
    )


if __name__ == "__main__":
    main()
