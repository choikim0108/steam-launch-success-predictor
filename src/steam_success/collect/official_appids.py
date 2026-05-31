from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

from steam_success.config import ProjectPaths, SETTINGS


USER_AGENT = "Mozilla/5.0 (compatible; academic-steam-success-predictor/1.0)"
OFFICIAL_APP_LIST_URL = "https://api.steampowered.com/IStoreService/GetAppList/v1/"


def load_api_key(root: Path) -> str:
    key = os.environ.get("STEAM_WEB_API_KEY", "").strip()
    env_path = root / ".env"
    if not key and env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("STEAM_WEB_API_KEY="):
                key = line.split("=", 1)[1].strip()
                break
    if not key or key.startswith("여기에_"):
        raise RuntimeError("STEAM_WEB_API_KEY is not set. Put it in .env or the current environment.")
    return key


def fetch_official_appids(
    api_key: str,
    max_apps: int,
    batch_size: int,
    sleep_seconds: float,
) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    rows: list[dict[str, object]] = []
    last_appid = 0

    while len(rows) < max_apps:
        payload: dict[str, object] = {
            "include_games": True,
            "include_dlc": False,
            "include_software": False,
            "include_videos": False,
            "include_hardware": False,
            "max_results": min(batch_size, max_apps - len(rows)),
        }
        if last_appid:
            payload["last_appid"] = last_appid

        response = session.get(
            OFFICIAL_APP_LIST_URL,
            params={"key": api_key, "format": "json", "input_json": json.dumps(payload)},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json().get("response", {})
        apps = data.get("apps") or []
        if not apps:
            break

        for app in apps:
            appid = app.get("appid")
            if appid is None:
                continue
            rows.append({
                "appid": int(appid),
                "official_name": app.get("name", ""),
                "last_modified": app.get("last_modified"),
                "price_change_number": app.get("price_change_number"),
                "source": "IStoreService/GetAppList",
            })
            if len(rows) >= max_apps:
                break

        last_appid = int(data.get("last_appid") or apps[-1].get("appid") or last_appid)
        if not data.get("have_more_results"):
            break
        time.sleep(sleep_seconds)

    if not rows:
        return pd.DataFrame(columns=["appid", "official_name", "last_modified", "price_change_number", "source"])
    return pd.DataFrame(rows).drop_duplicates("appid").reset_index(drop=True)


def run(root: Path, max_apps: int, batch_size: int, output_name: str) -> Path:
    paths = ProjectPaths.from_root(root)
    api_key = load_api_key(root)
    appids = fetch_official_appids(api_key, max_apps, batch_size, SETTINGS.request_sleep_seconds)
    output = paths.data_raw / output_name
    appids.to_csv(output, index=False)
    print(f"official_appid_rows={len(appids)}")
    print(f"max_apps={max_apps}")
    print(f"batch_size={batch_size}")
    print(f"output={output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect game appid candidates from official Steam IStoreService/GetAppList.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--max-apps", type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=10000)
    parser.add_argument("--output", default="steam_official_appids.csv")
    args = parser.parse_args()
    run(args.root.resolve(), args.max_apps, args.batch_size, args.output)


if __name__ == "__main__":
    main()
