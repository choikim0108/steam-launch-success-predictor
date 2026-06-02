from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
import requests

from steam_success.collect.steam import USER_AGENT
from steam_success.config import ProjectPaths, SETTINGS


def _load_appids(input_csv: Path, max_apps: int | None, only_label_eligible_90d: bool) -> list[int]:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    data = pd.read_csv(input_csv)
    if "appid" not in data.columns:
        raise ValueError(f"Input CSV must contain an appid column: {input_csv}")
    if only_label_eligible_90d:
        if "label_eligible_90d" not in data.columns:
            raise ValueError("--only-label-eligible-90d requires a label_eligible_90d column.")
        eligible = data["label_eligible_90d"].astype(str).str.lower().isin({"true", "1", "yes"})
        data = data[eligible]
    appids = data["appid"].dropna().astype(int).drop_duplicates().tolist()
    if max_apps is not None:
        appids = appids[:max_apps]
    if not appids:
        raise ValueError("No appids to collect.")
    return appids


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    return session


def _load_existing(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _completed_appids(status: pd.DataFrame) -> set[int]:
    if status.empty or "appid" not in status.columns or "histogram_success" not in status.columns:
        return set()
    success = status["histogram_success"].astype(str).str.lower().isin({"true", "1", "yes"})
    return set(status.loc[success, "appid"].dropna().astype(int).tolist())


def _successful_status_records(status: pd.DataFrame) -> list[dict[str, object]]:
    if status.empty or "histogram_success" not in status.columns:
        return []
    success = status["histogram_success"].astype(str).str.lower().isin({"true", "1", "yes"})
    return status.loc[success].to_dict("records")


def _request_json(
    session: requests.Session,
    appid: int,
    sleep_seconds: float,
    max_retries: int,
) -> dict[str, object]:
    url = f"https://store.steampowered.com/appreviewhistogram/{appid}"
    params = {"l": SETTINGS.language, "review_score_preference": 0}
    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, params=params, timeout=30)
            if response.status_code == 429 and attempt < max_retries:
                wait_seconds = sleep_seconds * (2**attempt)
                print(f"rate_limited appid={appid} retry={attempt + 1} wait_seconds={wait_seconds:.1f}")
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = str(exc)
            if attempt >= max_retries:
                break
            wait_seconds = sleep_seconds * (2**attempt)
            print(f"request_error appid={appid} retry={attempt + 1} wait_seconds={wait_seconds:.1f} error={last_error}")
            time.sleep(wait_seconds)
    raise RuntimeError(last_error)


def _rows_from_payload(appid: int, payload: dict[str, object]) -> tuple[list[dict[str, object]], dict[str, object]]:
    results = payload.get("results") or {}
    results = results if isinstance(results, dict) else {}
    rows: list[dict[str, object]] = []
    for index, item in enumerate(results.get("rollups") or [], start=1):
        if not isinstance(item, dict):
            continue
        up = int(item.get("recommendations_up") or 0)
        down = int(item.get("recommendations_down") or 0)
        rows.append(
            {
                "appid": appid,
                "bucket_index": index,
                "bucket_date_unix": int(item.get("date") or 0),
                "recommendations_up": up,
                "recommendations_down": down,
                "recommendations_total": up + down,
            }
        )
    status = {
        "appid": appid,
        "histogram_success": bool(payload.get("success")),
        "rollup_rows": len(rows),
        "histogram_start_date_unix": results.get("start_date", ""),
        "histogram_end_date_unix": results.get("end_date", ""),
        "count_all_reviews": payload.get("count_all_reviews", ""),
        "histogram_error": "",
    }
    return rows, status


def _collect_one(
    session: requests.Session,
    raw_dir: Path,
    appid: int,
    sleep_seconds: float,
    max_retries: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    raw_path = raw_dir / "review_histogram" / f"review_histogram_{appid}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if raw_path.exists():
            payload = json.loads(raw_path.read_text(encoding="utf-8"))
        else:
            payload = _request_json(session, appid, sleep_seconds, max_retries)
            raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(sleep_seconds)
        return _rows_from_payload(appid, payload)
    except Exception as exc:
        time.sleep(sleep_seconds)
        return [], {
            "appid": appid,
            "histogram_success": False,
            "rollup_rows": 0,
            "histogram_start_date_unix": "",
            "histogram_end_date_unix": "",
            "count_all_reviews": "",
            "histogram_error": str(exc),
        }


def run(
    root: Path,
    input_csv: Path,
    max_apps: int | None,
    flush_every: int,
    sleep_seconds: float,
    max_retries: int,
    only_label_eligible_90d: bool,
) -> None:
    paths = ProjectPaths.from_root(root)
    appids = _load_appids(input_csv, max_apps, only_label_eligible_90d)
    rows_output = paths.data_raw / "steam_review_histogram.csv"
    status_output = paths.data_raw / "steam_review_histogram_status.csv"
    existing_rows = _load_existing(rows_output)
    existing_status = _load_existing(status_output)
    done = _completed_appids(existing_status)
    all_rows = existing_rows.to_dict("records") if not existing_rows.empty else []
    status_rows = _successful_status_records(existing_status)
    session = _session()

    for index, appid in enumerate(appids, start=1):
        if appid not in done:
            rows, status = _collect_one(session, paths.data_raw, appid, sleep_seconds, max_retries)
            all_rows.extend(rows)
            status_rows.append(status)
            done.add(appid)
        if index % flush_every == 0:
            pd.DataFrame(all_rows).to_csv(rows_output, index=False)
            pd.DataFrame(status_rows).to_csv(status_output, index=False)
            print(f"checkpoint index={index} histogram_appids={len(done)} histogram_rows={len(all_rows)}")

    pd.DataFrame(all_rows).to_csv(rows_output, index=False)
    pd.DataFrame(status_rows).to_csv(status_output, index=False)
    print(f"appids={len(appids)}")
    print(f"histogram_appids={len(done)}")
    print(f"histogram_rows={len(all_rows)}")
    print(f"rows_output={rows_output}")
    print(f"status_output={status_output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Steam review histogram rollups for 7/30/90 day metrics.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--input-csv", type=Path, default=None)
    parser.add_argument("--max-apps", type=int, default=None)
    parser.add_argument("--flush-every", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--only-label-eligible-90d", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    input_csv = args.input_csv if args.input_csv is not None else root / "data" / "interim" / "game_candidates_2025_2026.csv"
    run(
        root,
        input_csv,
        args.max_apps,
        args.flush_every,
        args.sleep_seconds,
        args.max_retries,
        args.only_label_eligible_90d,
    )


if __name__ == "__main__":
    main()
