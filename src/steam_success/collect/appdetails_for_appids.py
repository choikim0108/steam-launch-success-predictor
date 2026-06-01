from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
import requests

from steam_success.collect.steam import USER_AGENT
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


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    return session


def _load_existing_rows(path: Path) -> dict[int, dict[str, object]]:
    if not path.exists():
        return {}
    data = pd.read_csv(path)
    if "appid" not in data.columns:
        return {}
    return {int(row["appid"]): dict(row) for row in data.to_dict("records")}


def _write_rows(rows_by_appid: dict[int, dict[str, object]], output: Path) -> None:
    frame = pd.DataFrame(rows_by_appid.values())
    if not frame.empty and "appid" in frame.columns:
        frame = frame.sort_values("appid").reset_index(drop=True)
    frame.to_csv(output, index=False)


def _detail_complete(row: dict[str, object] | None) -> bool:
    return bool(row and str(row.get("detail_success", "")).lower() == "true")


def _summary_complete(row: dict[str, object] | None) -> bool:
    return bool(row and str(row.get("review_success", "")).lower() == "true")


def _detail_row(appid: int, payload: dict[str, object]) -> dict[str, object]:
    item = payload.get(str(appid), {})
    item = item if isinstance(item, dict) else {}
    data = item.get("data") or {}
    data = data if isinstance(data, dict) else {}
    price = data.get("price_overview") or {}
    price = price if isinstance(price, dict) else {}
    release_date = data.get("release_date") or {}
    release_date = release_date if isinstance(release_date, dict) else {}
    platforms = data.get("platforms") or {}
    platforms = platforms if isinstance(platforms, dict) else {}
    metacritic = data.get("metacritic") or {}
    metacritic = metacritic if isinstance(metacritic, dict) else {}
    recommendations = data.get("recommendations") or {}
    recommendations = recommendations if isinstance(recommendations, dict) else {}
    return {
        "appid": appid,
        "detail_success": bool(item.get("success")) and bool(data),
        "name": data.get("name", ""),
        "type": data.get("type", ""),
        "is_free": bool(data.get("is_free", False)),
        "required_age": data.get("required_age", 0),
        "release_date_text": release_date.get("date", ""),
        "coming_soon": bool(release_date.get("coming_soon", False)),
        "price_initial_usd": price.get("initial", 0) / 100 if price else 0.0,
        "price_final_usd": price.get("final", 0) / 100 if price else 0.0,
        "discount_percent": price.get("discount_percent", 0) if price else 0,
        "developers": ", ".join(data.get("developers") or []),
        "publishers": ", ".join(data.get("publishers") or []),
        "genres": ", ".join(g.get("description", "") for g in data.get("genres") or []),
        "categories": ", ".join(c.get("description", "") for c in data.get("categories") or []),
        "platform_windows": bool(platforms.get("windows", False)),
        "platform_mac": bool(platforms.get("mac", False)),
        "platform_linux": bool(platforms.get("linux", False)),
        "metacritic_score": metacritic.get("score"),
        "recommendations_total": recommendations.get("total"),
        "supported_languages_raw": data.get("supported_languages", ""),
    }


def _summary_row(appid: int, payload: dict[str, object]) -> dict[str, object]:
    summary = payload.get("query_summary") or {}
    summary = summary if isinstance(summary, dict) else {}
    total = int(summary.get("total_reviews") or 0)
    positive = int(summary.get("total_positive") or 0)
    negative = int(summary.get("total_negative") or 0)
    return {
        "appid": appid,
        "review_success": bool(payload.get("success", 1)),
        "review_score": int(summary.get("review_score") or 0),
        "review_score_desc": summary.get("review_score_desc", ""),
        "total_reviews": total,
        "total_positive": positive,
        "total_negative": negative,
        "positive_rate": positive / total if total else 0.0,
    }


def _request_json(
    session: requests.Session,
    url: str,
    params: dict[str, object],
    sleep_seconds: float,
    max_retries: int,
) -> dict[str, object]:
    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, params=params, timeout=30)
            if response.status_code == 429 and attempt < max_retries:
                wait_seconds = sleep_seconds * (2 ** attempt)
                print(f"rate_limited url={url} retry={attempt + 1} wait_seconds={wait_seconds:.1f}")
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = str(exc)
            if attempt >= max_retries:
                break
            wait_seconds = sleep_seconds * (2 ** attempt)
            print(f"request_error url={url} retry={attempt + 1} wait_seconds={wait_seconds:.1f} error={last_error}")
            time.sleep(wait_seconds)
    raise RuntimeError(last_error)


def _collect_appdetails(
    session: requests.Session,
    raw_dir: Path,
    appid: int,
    sleep_seconds: float,
    max_retries: int,
) -> dict[str, object]:
    raw_path = raw_dir / f"appdetails_{appid}.json"
    if raw_path.exists():
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        return _detail_row(appid, payload)
    url = "https://store.steampowered.com/api/appdetails"
    params = {"appids": appid, "cc": SETTINGS.country, "l": SETTINGS.language}
    try:
        payload = _request_json(session, url, params, sleep_seconds, max_retries)
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(sleep_seconds)
        return _detail_row(appid, payload)
    except Exception as exc:
        time.sleep(sleep_seconds)
        return {"appid": appid, "detail_success": False, "detail_error": str(exc)}


def _collect_review_summary(
    session: requests.Session,
    raw_dir: Path,
    appid: int,
    sleep_seconds: float,
    max_retries: int,
) -> dict[str, object]:
    raw_path = raw_dir / f"review_summary_{appid}.json"
    if raw_path.exists():
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        return _summary_row(appid, payload)
    url = f"https://store.steampowered.com/appreviews/{appid}"
    params = {"json": 1, "filter": "summary", "language": "all", "purchase_type": "all", "num_per_page": 0}
    try:
        payload = _request_json(session, url, params, sleep_seconds, max_retries)
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(sleep_seconds)
        return _summary_row(appid, payload)
    except Exception as exc:
        time.sleep(sleep_seconds)
        return {"appid": appid, "review_success": False, "review_error": str(exc)}


def run(
    root: Path,
    input_csv: Path,
    max_apps: int | None,
    flush_every: int,
    sleep_seconds: float,
    max_retries: int,
) -> None:
    paths = ProjectPaths.from_root(root)
    appids = _load_appids(input_csv, max_apps)
    details_output = paths.data_raw / "steam_appdetails.csv"
    summaries_output = paths.data_raw / "steam_review_summaries.csv"
    detail_rows = _load_existing_rows(details_output)
    summary_rows = _load_existing_rows(summaries_output)
    session = _session()

    for index, appid in enumerate(appids, start=1):
        if not _detail_complete(detail_rows.get(appid)):
            detail_rows[appid] = _collect_appdetails(session, paths.data_raw, appid, sleep_seconds, max_retries)
        if not _summary_complete(summary_rows.get(appid)):
            summary_rows[appid] = _collect_review_summary(session, paths.data_raw, appid, sleep_seconds, max_retries)
        if index % flush_every == 0:
            _write_rows(detail_rows, details_output)
            _write_rows(summary_rows, summaries_output)
            print(f"checkpoint index={index} details_rows={len(detail_rows)} review_summary_rows={len(summary_rows)}")

    _write_rows(detail_rows, details_output)
    _write_rows(summary_rows, summaries_output)
    print(f"appids={len(appids)}")
    print(f"details_rows={len(detail_rows)}")
    print(f"review_summary_rows={len(summary_rows)}")
    print(f"detail_success_rows={sum(1 for row in detail_rows.values() if _detail_complete(row))}")
    print(f"review_success_rows={sum(1 for row in summary_rows.values() if _summary_complete(row))}")
    print(f"details_output={details_output}")
    print(f"review_summaries_output={summaries_output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect appdetails and review summaries for an existing appid CSV.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--input-csv", type=Path, default=None)
    parser.add_argument("--max-apps", type=int, default=None)
    parser.add_argument("--flush-every", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-retries", type=int, default=5)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.input_csv is not None:
        input_csv = args.input_csv
    else:
        search_window_csv = root / "data" / "interim" / "search_release_window_appids.csv"
        official_csv = root / "data" / "raw" / "steam_official_appids.csv"
        steamspy_csv = root / "data" / "raw" / "steamspy_appids.csv"
        if search_window_csv.exists():
            input_csv = search_window_csv
        elif official_csv.exists():
            input_csv = official_csv
        else:
            input_csv = steamspy_csv
    run(root, input_csv, args.max_apps, args.flush_every, args.sleep_seconds, args.max_retries)


if __name__ == "__main__":
    main()
