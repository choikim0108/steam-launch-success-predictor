from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from steam_success.collect.steam import CrawlConfig, fetch_appdetails, fetch_review_summaries
from steam_success.config import ProjectPaths, SETTINGS


def _load_appids(input_csv: Path, max_apps: int | None) -> list[int]:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    data = pd.read_csv(input_csv)
    if "appid" not in data.columns:
        raise ValueError(f"Input CSV must contain an appid column: {input_csv}")
    appids = data["appid"].dropna().astype(int).drop_duplicates().tolist()
    if max_apps is not None:
        appids = appids[:max_apps]
    if not appids:
        raise ValueError("No appids to collect.")
    return appids


def run(root: Path, input_csv: Path, max_apps: int | None) -> None:
    paths = ProjectPaths.from_root(root)
    appids = _load_appids(input_csv, max_apps)
    config = CrawlConfig(
        max_apps=len(appids),
        pages=SETTINGS.search_pages,
        sleep_seconds=SETTINGS.request_sleep_seconds,
        country=SETTINGS.country,
        language=SETTINGS.language,
    )
    details = fetch_appdetails(appids, paths.data_raw, config)
    summaries = fetch_review_summaries(appids, paths.data_raw, config)
    details_output = paths.data_raw / "steam_appdetails.csv"
    summaries_output = paths.data_raw / "steam_review_summaries.csv"
    details.to_csv(details_output, index=False)
    summaries.to_csv(summaries_output, index=False)
    print(f"appids={len(appids)}")
    print(f"details_rows={len(details)}")
    print(f"review_summary_rows={len(summaries)}")
    print(f"details_output={details_output}")
    print(f"review_summaries_output={summaries_output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect appdetails and review summaries for an existing appid CSV.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--input-csv", type=Path, default=None)
    parser.add_argument("--max-apps", type=int, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    input_csv = args.input_csv if args.input_csv is not None else root / "data" / "raw" / "steamspy_appids.csv"
    run(root, input_csv, args.max_apps)


if __name__ == "__main__":
    main()
