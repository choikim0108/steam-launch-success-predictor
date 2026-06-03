from __future__ import annotations

import json
import re
import time
from html import unescape
from pathlib import Path
from typing import cast
from urllib.parse import quote_plus

import pandas as pd
import requests

from steam_success.config import ProjectSettings, SETTINGS


USER_AGENT = "Mozilla/5.0 (compatible; academic-steam-success-predictor/1.0)"
WEBZINE_FEEDS = (
    "https://www.pcgamer.com/rss/",
    "https://www.gamespot.com/feeds/mashup/",
)


def _search_html(query: str) -> str:
    urls = [
        f"https://duckduckgo.com/html/?q={quote_plus(query)}",
        f"https://www.bing.com/search?q={quote_plus(query)}",
    ]
    last_error: Exception | None = None
    for url in urls:
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            last_error = exc
    raise RuntimeError(str(last_error))


def _youtube_html(name: str) -> str:
    url = f"https://www.youtube.com/results?search_query={quote_plus(name + ' game')}"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12)
    response.raise_for_status()
    return response.text


def _steamspy_owners_median(appid: int) -> int:
    response = requests.get("https://steamspy.com/api.php", params={"request": "appdetails", "appid": appid}, headers={"User-Agent": USER_AGENT}, timeout=12)
    response.raise_for_status()
    owners = str(response.json().get("owners", ""))
    numbers = [int(part.replace(",", "")) for part in re.findall(r"[0-9,]+", owners)]
    if len(numbers) < 2:
        return 0
    return int(sum(numbers[:2]) / 2)


def _result_count(html: str) -> int:
    duck_count = len(re.findall(r'class="result__a"', html))
    bing_count = len(re.findall(r'<li class="b_algo"', html))
    youtube_count = len(re.findall(r'"videoRenderer"', html))
    return max(duck_count, bing_count, youtube_count)


def _top_titles(html: str, limit: int = 3) -> str:
    title_patterns = [
        r'class="result__a"[^>]*>(.*?)</a>',
        r'<h2[^>]*>\s*<a[^>]*>(.*?)</a>',
        r'"title":\{"runs":\[\{"text":"(.*?)"',
    ]
    titles: list[str] = []
    for pattern in title_patterns:
        titles.extend(re.findall(pattern, html, flags=re.DOTALL))
    cleaned = [re.sub(r"<[^>]+>", "", unescape(title)).strip() for title in titles]
    return " | ".join([title for title in cleaned if title][:limit])


def _webzine_mentions(name: str, domains: tuple[str, ...]) -> tuple[int, str]:
    gdelt_count, gdelt_titles = _gdelt_webzine_mentions(name, domains)
    if gdelt_count:
        return gdelt_count, gdelt_titles
    titles: list[str] = []
    query = " OR ".join([f'site:{domain}' for domain in domains])
    html = _search_html(f'"{name}" game review ({query})')
    total = _result_count(html)
    domain_titles = _top_titles(html, limit=3)
    if domain_titles:
        titles.append(domain_titles)
    return total, " | ".join(titles[:3])


def _gdelt_webzine_mentions(name: str, domains: tuple[str, ...]) -> tuple[int, str]:
    domain_query = " OR ".join([f"domain:{domain}" for domain in domains])
    query = f'"{name}" game review ({domain_query})'
    response = requests.get(
        "https://api.gdeltproject.org/api/v2/doc/doc",
        params={"query": query, "mode": "artlist", "format": "json", "maxrecords": 10, "sort": "hybridrel"},
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    articles = response.json().get("articles", [])
    titles = [str(article.get("title", "")).strip() for article in articles if str(article.get("title", "")).strip()]
    return len(articles), " | ".join(titles[:3])


def _webzine_source_count() -> int:
    count = 0
    for url in WEBZINE_FEEDS:
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8)
            response.raise_for_status()
            if "<item" in response.text:
                count += 1
        except Exception:
            pass
    return count


def collect_external_web_signals(dataset: pd.DataFrame, raw_dir: Path, settings: ProjectSettings = SETTINGS) -> pd.DataFrame:
    """Collect no-key public web mention signals for a limited game sample.

    This intentionally stores mention counts, not YouTube likes/dislikes. YouTube dislike ratios are not
    publicly available from normal no-key web crawling.
    """
    rows: list[dict[str, object]] = []
    sample = dataset[["appid", "name"]].dropna().drop_duplicates().head(settings.external_signal_sample_size)
    external_dir = raw_dir / "external_web"
    external_dir.mkdir(parents=True, exist_ok=True)
    webzine_source_count = _webzine_source_count()
    for row in cast(list[dict[str, object]], cast(pd.DataFrame, sample).to_dict(orient="records")):
        appid = int(str(row["appid"]))
        name = str(row["name"])
        queries = {
            "youtube_mentions": f'"{name}" game site:{settings.youtube_search_domain}',
            "blog_mentions": " OR ".join([f'"{name}" game site:{domain}' for domain in settings.blog_domains]),
        }
        record: dict[str, object] = {"appid": appid, "external_signal_success": True, "webzine_source_count": webzine_source_count}
        titles: dict[str, str] = {}
        for key, query in queries.items():
            try:
                html = _youtube_html(name) if key == "youtube_mentions" else _search_html(query)
                safe_key = re.sub(r"[^a-z0-9_]+", "_", key.lower())
                (external_dir / f"{appid}_{safe_key}.html").write_text(html, encoding="utf-8")
                record[key] = _result_count(html)
                titles[key] = _top_titles(html)
            except Exception as exc:
                record[key] = 0
                record["external_signal_success"] = False
                record[f"{key}_error"] = str(exc)
            time.sleep(settings.external_request_sleep_seconds)
        try:
            webzine_count, webzine_titles = _webzine_mentions(name, settings.webzine_domains)
            record["webzine_mentions"] = webzine_count
            titles["webzine_mentions"] = webzine_titles
        except Exception as exc:
            record["webzine_mentions"] = 0
            record["external_signal_success"] = False
            record["webzine_mentions_error"] = str(exc)
        try:
            record["steamspy_owners_median"] = _steamspy_owners_median(appid)
        except Exception as exc:
            record["steamspy_owners_median"] = 0
            record["steamspy_error"] = str(exc)
        record["external_top_titles_json"] = json.dumps(titles, ensure_ascii=False)
        rows.append(record)
    signals = pd.DataFrame(rows)
    if signals.empty:
        signals = pd.DataFrame(columns=["appid", "external_signal_success", "youtube_mentions", "webzine_mentions", "blog_mentions", "external_top_titles_json"])
    for col in ["youtube_mentions", "webzine_mentions", "blog_mentions"]:
        if col not in signals.columns:
            signals[col] = 0
    signals["external_attention_score"] = signals[["youtube_mentions", "webzine_mentions", "blog_mentions"]].sum(axis=1)
    signals.to_csv(raw_dir / "external_web_signals.csv", index=False)
    return signals
