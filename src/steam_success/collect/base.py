from __future__ import annotations

import argparse
from pathlib import Path

from steam_success.collect.steam import collect_all
from steam_success.config import ProjectPaths, SETTINGS


def run(root: Path, max_apps: int | None = None) -> None:
    paths = ProjectPaths.from_root(root)
    collected = collect_all(paths, settings=SETTINGS, max_apps=max_apps)
    search_rows = len(collected["search"])
    detail_rows = len(collected["details"])
    review_rows = len(collected["reviews"])
    print("base Steam collection completed")
    print(f"search_rows={search_rows}")
    print(f"detail_rows={detail_rows}")
    print(f"review_summary_rows={review_rows}")
    print(f"raw_dir={paths.data_raw}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Steam appids, appdetails, and review summaries without training legacy models.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--max-apps", type=int, default=None, help="Override SETTINGS.max_apps for this collection run")
    args = parser.parse_args()
    run(args.root.resolve(), args.max_apps)


if __name__ == "__main__":
    main()
