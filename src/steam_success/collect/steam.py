from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Iterable
from typing import TypedDict

import pandas as pd
import requests
from bs4 import BeautifulSoup

from steam_success.config import ProjectPaths, ProjectSettings, SETTINGS


USER_AGENT = "Mozilla/5.0 (compatible; academic-steam-success-predictor/1.0)"


@dataclass
class CrawlConfig:
    max_apps: int
    pages: int
    sleep_seconds: float
    country: str
    language: str


class CollectionResult(TypedDict):
    search: pd.DataFrame
    details: pd.DataFrame
    reviews: pd.DataFrame
    config: CrawlConfig


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    return session


def crawl_search_appids(config: CrawlConfig, raw_dir: Path) -> pd.DataFrame:
    session = _session()
    rows: list[dict[str, object]] = []
    seen: set[int] = set()
    for page in range(1, config.pages + 1):
        url = "https://store.steampowered.com/search/"
        params = {
            "filter": "popularnew",
            "sort_by": "Released_DESC",
            "ignore_preferences": "1",
            "ndl": "1",
            "page": page,
            "cc": config.country,
            "l": config.language,
        }
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        (raw_dir / f"steam_search_page_{page}.html").write_text(response.text, encoding="utf-8")
        soup = BeautifulSoup(response.text, "lxml")
        for anchor in soup.select("a.search_result_row"):
            raw_appid = anchor.get("data-ds-appid") or anchor.get("data-ds-bundleid")
            if not raw_appid:
                continue
            try:
                appid = int(str(raw_appid).split(",")[0])
            except ValueError:
                continue
            if appid in seen:
                continue
            seen.add(appid)
            title_el = anchor.select_one("span.title")
            release_el = anchor.select_one("div.search_released")
            price_el = anchor.select_one("div.discount_final_price")
            rows.append({
                "appid": appid,
                "search_name": title_el.get_text(strip=True) if title_el else "",
                "search_release_text": release_el.get_text(strip=True) if release_el else "",
                "search_price_text": price_el.get_text(strip=True) if price_el else "",
                "search_page": page,
                "source_url": response.url,
            })
            if len(rows) >= config.max_apps:
                return pd.DataFrame(rows)
        time.sleep(config.sleep_seconds)
    return pd.DataFrame(rows)


def fetch_appdetails(appids: Iterable[int], raw_dir: Path, config: CrawlConfig) -> pd.DataFrame:
    session = _session()
    rows: list[dict[str, object]] = []
    for appid in appids:
        cached = raw_dir / f"appdetails_{appid}.json"
        url = "https://store.steampowered.com/api/appdetails"
        params = {"appids": appid, "cc": config.country, "l": config.language}
        try:
            if cached.exists():
                payload = json.loads(cached.read_text(encoding="utf-8"))
            else:
                response = session.get(url, params=params, timeout=30)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            rows.append({"appid": appid, "detail_success": False, "detail_error": str(exc)})
            continue
        cached.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        item = payload.get(str(appid), {})
        data = item.get("data") or {}
        price = data.get("price_overview") or {}
        rows.append({
            "appid": appid,
            "detail_success": bool(item.get("success")) and bool(data),
            "name": data.get("name", ""),
            "type": data.get("type", ""),
            "is_free": bool(data.get("is_free", False)),
            "required_age": data.get("required_age", 0),
            "release_date_text": (data.get("release_date") or {}).get("date", ""),
            "coming_soon": bool((data.get("release_date") or {}).get("coming_soon", False)),
            "price_initial_usd": price.get("initial", 0) / 100 if price else 0.0,
            "price_final_usd": price.get("final", 0) / 100 if price else 0.0,
            "discount_percent": price.get("discount_percent", 0) if price else 0,
            "developers": ", ".join(data.get("developers") or []),
            "publishers": ", ".join(data.get("publishers") or []),
            "header_image": data.get("header_image", ""),
            "genres": ", ".join(g.get("description", "") for g in data.get("genres") or []),
            "categories": ", ".join(c.get("description", "") for c in data.get("categories") or []),
            "platform_windows": bool((data.get("platforms") or {}).get("windows", False)),
            "platform_mac": bool((data.get("platforms") or {}).get("mac", False)),
            "platform_linux": bool((data.get("platforms") or {}).get("linux", False)),
            "metacritic_score": (data.get("metacritic") or {}).get("score"),
            "recommendations_total": (data.get("recommendations") or {}).get("total"),
            "supported_languages_raw": data.get("supported_languages", ""),
        })
        time.sleep(config.sleep_seconds)
    return pd.DataFrame(rows)


def fetch_review_summaries(appids: Iterable[int], raw_dir: Path, config: CrawlConfig) -> pd.DataFrame:
    session = _session()
    rows: list[dict[str, object]] = []
    for appid in appids:
        cached = raw_dir / f"review_summary_{appid}.json"
        url = f"https://store.steampowered.com/appreviews/{appid}"
        params = {"json": 1, "filter": "summary", "language": "all", "purchase_type": "all", "num_per_page": 0}
        try:
            if cached.exists():
                payload = json.loads(cached.read_text(encoding="utf-8"))
            else:
                response = session.get(url, params=params, timeout=30)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            rows.append({"appid": appid, "review_success": False, "review_error": str(exc)})
            continue
        cached.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = payload.get("query_summary") or {}
        total = int(summary.get("total_reviews") or 0)
        positive = int(summary.get("total_positive") or 0)
        negative = int(summary.get("total_negative") or 0)
        rows.append({
            "appid": appid,
            "review_success": bool(payload.get("success", 1)),
            "review_score": int(summary.get("review_score") or 0),
            "review_score_desc": summary.get("review_score_desc", ""),
            "total_reviews": total,
            "total_positive": positive,
            "total_negative": negative,
            "positive_rate": positive / total if total else 0.0,
        })
        time.sleep(config.sleep_seconds)
    return pd.DataFrame(rows)


def fetch_review_texts(appids: Iterable[int], raw_dir: Path, config: CrawlConfig, per_game: int) -> pd.DataFrame:
    session = _session()
    rows: list[dict[str, object]] = []
    text_dir = raw_dir / "review_texts"
    text_dir.mkdir(parents=True, exist_ok=True)
    for appid in appids:
        url = f"https://store.steampowered.com/appreviews/{appid}"
        params = {
            "json": 1,
            "filter": "recent",
            "language": "all",
            "purchase_type": "all",
            "num_per_page": per_game,
        }
        try:
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            rows.append({"appid": int(appid), "review_collection_success": False, "review_error": str(exc)})
            continue
        (text_dir / f"review_texts_{int(appid)}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        for item in payload.get("reviews") or []:
            author = item.get("author") or {}
            rows.append({
                "appid": int(appid),
                "review_collection_success": True,
                "review_id": str(item.get("recommendationid", "")),
                "voted_up": bool(item.get("voted_up", False)),
                "review_text": str(item.get("review", "")).replace("\r", " ").replace("\n", " ").strip(),
                "playtime_hours": float(author.get("playtime_forever") or 0) / 60,
                "timestamp_created": int(item.get("timestamp_created") or 0),
            })
        time.sleep(config.sleep_seconds)
    return pd.DataFrame(rows)


def fetch_review_timeline(
    appids: Iterable[int],
    raw_dir: Path,
    config: CrawlConfig,
    page_size: int,
    max_reviews_per_game: int,
) -> pd.DataFrame:
    session = _session()
    rows: list[dict[str, object]] = []
    timeline_dir = raw_dir / "review_timeline"
    timeline_dir.mkdir(parents=True, exist_ok=True)
    per_page = max(1, min(page_size, 100))
    for appid in appids:
        cursor = "*"
        seen_cursors: set[str] = set()
        collected = 0
        page_index = 1
        while collected < max_reviews_per_game and cursor not in seen_cursors:
            seen_cursors.add(cursor)
            url = f"https://store.steampowered.com/appreviews/{int(appid)}"
            params = {
                "json": 1,
                "filter": "recent",
                "language": "all",
                "purchase_type": "all",
                "num_per_page": min(per_page, max_reviews_per_game - collected),
                "cursor": cursor,
            }
            try:
                response = session.get(url, params=params, timeout=30)
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                rows.append({
                    "appid": int(appid),
                    "timeline_collection_success": False,
                    "timeline_error": str(exc),
                })
                break
            (timeline_dir / f"review_timeline_{int(appid)}_page_{page_index}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            reviews = payload.get("reviews") or []
            if not reviews:
                break
            for item in reviews:
                author = item.get("author") or {}
                rows.append({
                    "appid": int(appid),
                    "timeline_collection_success": True,
                    "review_id": str(item.get("recommendationid", "")),
                    "voted_up": bool(item.get("voted_up", False)),
                    "review_text": str(item.get("review", "")).replace("\r", " ").replace("\n", " ").strip(),
                    "playtime_hours": float(author.get("playtime_forever") or 0) / 60,
                    "timestamp_created": int(item.get("timestamp_created") or 0),
                    "timestamp_updated": int(item.get("timestamp_updated") or 0),
                    "weighted_vote_score": float(item.get("weighted_vote_score") or 0),
                    "votes_up": int(item.get("votes_up") or 0),
                    "votes_funny": int(item.get("votes_funny") or 0),
                    "review_page": page_index,
                })
            collected += len(reviews)
            next_cursor = str(payload.get("cursor") or "")
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor
            page_index += 1
            time.sleep(config.sleep_seconds)
    return pd.DataFrame(rows)


def collect_all(paths: ProjectPaths, settings: ProjectSettings = SETTINGS, max_apps: int | None = None) -> CollectionResult:
    config = CrawlConfig(
        max_apps=max_apps if max_apps is not None else settings.max_apps,
        pages=settings.search_pages,
        sleep_seconds=settings.request_sleep_seconds,
        country=settings.country,
        language=settings.language,
    )
    (paths.data_raw / "crawl_config.json").write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
    search = crawl_search_appids(config, paths.data_raw)
    if search.empty:
        raise RuntimeError("Steam search crawling returned no appids.")
    appids = search["appid"].drop_duplicates().astype(int).tolist()
    details = fetch_appdetails(appids, paths.data_raw, config)
    reviews = fetch_review_summaries(appids, paths.data_raw, config)
    search.to_csv(paths.data_raw / "steam_search_crawl.csv", index=False)
    details.to_csv(paths.data_raw / "steam_appdetails.csv", index=False)
    reviews.to_csv(paths.data_raw / "steam_review_summaries.csv", index=False)
    return {"search": search, "details": details, "reviews": reviews, "config": config}
