from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from steam_success.collect.steam import USER_AGENT
from steam_success.config import ProjectPaths, SETTINGS


SEARCH_RESULTS_URL = "https://store.steampowered.com/search/results/"


def release_year(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"(19\d{2}|20\d{2})", value)
    return int(match.group(1)) if match else None


def release_window_role(year: int | None, start_year: int, end_year: int) -> str:
    if year is None:
        return "unknown"
    if year == 2026:
        return "2026_trend"
    if year == 2025:
        return "2025_trend_label_candidate"
    if start_year <= year <= end_year:
        return "in_window"
    return "out_of_range"


def release_year_bucket(year: int | None, start_year: int, end_year: int) -> str:
    if year is None:
        return "unknown"
    if start_year <= year <= end_year:
        return str(year)
    return "out_of_range"


def _resolve_output(root: Path, paths: ProjectPaths, output: str) -> Path:
    output_path = Path(output)
    if output_path.is_absolute():
        return output_path
    if len(output_path.parts) > 1:
        return root / output_path
    return paths.data_interim / output_path


def _fetch_search_page(
    session: requests.Session,
    start: int,
    count: int,
    country: str,
    language: str,
    sleep_seconds: float,
    max_retries: int,
) -> tuple[dict[str, object], str]:
    params = {
        "query": "",
        "start": start,
        "count": count,
        "dynamic_data": "",
        "sort_by": "Released_DESC",
        "category1": "998",
        "ignore_preferences": "1",
        "ndl": "1",
        "cc": country,
        "l": language,
        "infinite": "1",
    }
    for attempt in range(max_retries + 1):
        response = session.get(SEARCH_RESULTS_URL, params=params, timeout=30)
        if response.status_code != 429:
            response.raise_for_status()
            return response.json(), response.url
        wait_seconds = sleep_seconds * (2 ** attempt)
        print(f"rate_limited_start={start} retry={attempt + 1} wait_seconds={wait_seconds:.1f}")
        time.sleep(wait_seconds)
    response.raise_for_status()
    raise RuntimeError("unreachable")


def _parse_rows(
    payload: dict[str, object],
    source_url: str,
    start: int,
    start_year: int,
    end_year: int,
) -> list[dict[str, object]]:
    soup = BeautifulSoup(str(payload.get("results_html") or ""), "lxml")
    rows: list[dict[str, object]] = []
    for anchor in soup.select("a.search_result_row"):
        raw_appid = anchor.get("data-ds-appid")
        if not raw_appid:
            continue
        try:
            appid = int(str(raw_appid).split(",")[0])
        except ValueError:
            continue
        title_el = anchor.select_one("span.title")
        release_el = anchor.select_one("div.search_released")
        price_el = anchor.select_one("div.discount_final_price")
        release_text = release_el.get_text(strip=True) if release_el else ""
        year = release_year(release_text)
        rows.append({
            "appid": appid,
            "search_name": title_el.get_text(strip=True) if title_el else "",
            "search_release_text": release_text,
            "search_release_year": year,
            "release_year_bucket": release_year_bucket(year, start_year, end_year),
            "release_window_role": release_window_role(year, start_year, end_year),
            "search_price_text": price_el.get_text(strip=True) if price_el else "",
            "start": start,
            "source_url": source_url,
        })
    return rows


def collect_release_window(
    root: Path,
    start_year: int,
    end_year: int,
    stop_before_year: int,
    count: int,
    sleep_seconds: float,
    max_pages: int | None,
    output: str,
    stop_pages: int,
    max_retries: int,
    start_offset: int,
) -> Path:
    paths = ProjectPaths.from_root(root)
    output_path = _resolve_output(root, paths, output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw_dir = paths.data_raw / "search_release_window"
    raw_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    if output_path.exists():
        existing = pd.read_csv(output_path)
        rows.extend(existing.to_dict("records"))
        next_start = int(existing["start"].max()) + count if "start" in existing.columns and not existing.empty else 0
    else:
        next_start = start_offset

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    consecutive_before_window_pages = 0
    pages_fetched = 0
    total_count: int | None = None

    while max_pages is None or pages_fetched < max_pages:
        payload, source_url = _fetch_search_page(
            session,
            next_start,
            count,
            SETTINGS.country,
            SETTINGS.language,
            sleep_seconds,
            max_retries,
        )
        total_count = int(payload.get("total_count") or total_count or 0)
        (raw_dir / f"search_results_start_{next_start}.json").write_text(
            json.dumps({"source_url": source_url, "payload": payload}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        page_rows = _parse_rows(payload, source_url, next_start, start_year, end_year)
        if not page_rows:
            break

        rows.extend(page_rows)
        frame = pd.DataFrame(rows).drop_duplicates("appid").reset_index(drop=True)
        frame.to_csv(output_path, index=False)

        page_years = [row["search_release_year"] for row in page_rows if row["search_release_year"] is not None]
        if page_years and max(page_years) < stop_before_year:
            consecutive_before_window_pages += 1
        else:
            consecutive_before_window_pages = 0
        pages_fetched += 1

        print(
            f"start={next_start} rows={len(page_rows)} total_rows={len(frame)} "
            f"min_year={min(page_years) if page_years else ''} max_year={max(page_years) if page_years else ''}"
        )
        if consecutive_before_window_pages >= stop_pages:
            print(f"stop_reason=before_{stop_before_year}_for_{stop_pages}_pages")
            break
        if total_count and next_start + count >= total_count:
            print("stop_reason=end_of_search_results")
            break

        next_start += count
        time.sleep(sleep_seconds)

    print(f"output={output_path}")
    print(f"total_count={total_count if total_count is not None else ''}")
    print(f"pages_fetched={pages_fetched}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Steam search appids across a release-year window.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--start-year", type=int, default=2025)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--stop-before-year", type=int, default=2025)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=1.5)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--stop-pages", type=int, default=2)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--start-offset", type=int, default=0, help="Search result offset to start from when no checkpoint exists.")
    parser.add_argument("--output", default="data/interim/search_release_window_appids.csv")
    args = parser.parse_args()
    collect_release_window(
        root=args.root.resolve(),
        start_year=args.start_year,
        end_year=args.end_year,
        stop_before_year=args.stop_before_year,
        count=args.count,
        sleep_seconds=args.sleep_seconds,
        max_pages=args.max_pages,
        output=args.output,
        stop_pages=args.stop_pages,
        max_retries=args.max_retries,
        start_offset=args.start_offset,
    )


if __name__ == "__main__":
    main()
