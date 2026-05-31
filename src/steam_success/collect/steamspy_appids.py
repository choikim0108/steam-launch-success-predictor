from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import requests

from steam_success.config import ProjectPaths, SETTINGS


USER_AGENT = "Mozilla/5.0 (compatible; academic-steam-success-predictor/1.0)"


def fetch_steamspy_pages(pages: int, sleep_seconds: float) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    rows: list[dict[str, object]] = []
    for page in range(pages):
        url = "https://steamspy.com/api.php"
        response = session.get(url, params={"request": "all", "page": page}, timeout=60)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not payload:
            break
        for appid, item in payload.items():
            record = dict(item)
            record["appid"] = int(appid)
            record["steamspy_page"] = page
            rows.append(record)
        time.sleep(sleep_seconds)
    if not rows:
        return pd.DataFrame(columns=["appid", "name", "steamspy_page"])
    return pd.DataFrame(rows).drop_duplicates("appid").reset_index(drop=True)


def run(root: Path, pages: int, output_name: str) -> Path:
    paths = ProjectPaths.from_root(root)
    appids = fetch_steamspy_pages(pages, SETTINGS.request_sleep_seconds)
    output = paths.data_raw / output_name
    appids.to_csv(output, index=False)
    print(f"steamspy_rows={len(appids)}")
    print(f"pages={pages}")
    print(f"output={output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect appid candidates from SteamSpy all pages.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--pages", type=int, default=1, help="SteamSpy pages to fetch. Each page returns up to 1000 rows.")
    parser.add_argument("--output", default="steamspy_appids.csv")
    args = parser.parse_args()
    run(args.root.resolve(), args.pages, args.output)


if __name__ == "__main__":
    main()
