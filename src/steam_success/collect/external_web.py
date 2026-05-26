from __future__ import annotations

import json
import re
import time
from html import unescape
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import requests

from steam_success.config import ProjectSettings, SETTINGS


USER_AGENT = "Mozilla/5.0 (compatible; academic-steam-success-predictor/1.0)"


def _search_html(query: str) -> str:
    urls = [
        f"https://duckduckgo.com/html/?q={quote_plus(query)}",
        f"https://www.bing.com/search?q={quote_plus(query)}",
    ]
    last_error: Exception | None = None
    for url in urls:
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12)
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


def collect_external_web_signals(dataset: pd.DataFrame, raw_dir: Path, settings: ProjectSettings = SETTINGS) -> pd.DataFrame:
    """Collect no-key public web mention signals for a limited game sample.

    This intentionally stores mention counts, not YouTube likes/dislikes. YouTube dislike ratios are not
    publicly available from normal no-key web crawling.
    """
    rows: list[dict[str, object]] = []
    sample = dataset[["appid", "name"]].dropna().drop_duplicates().head(settings.external_signal_sample_size)
    external_dir = raw_dir / "external_web"
    external_dir.mkdir(parents=True, exist_ok=True)
    for row in sample.itertuples(index=False):
        name = str(row.name)
        queries = {
            "youtube_mentions": f'"{name}" game site:{settings.youtube_search_domain}',
            "webzine_mentions": " OR ".join([f'"{name}" game site:{domain}' for domain in settings.webzine_domains]),
            "blog_mentions": " OR ".join([f'"{name}" game site:{domain}' for domain in settings.blog_domains]),
        }
        record: dict[str, object] = {"appid": int(row.appid), "external_signal_success": True}
        titles: dict[str, str] = {}
        for key, query in queries.items():
            try:
                html = _youtube_html(name) if key == "youtube_mentions" else _search_html(query)
                safe_key = re.sub(r"[^a-z0-9_]+", "_", key.lower())
                (external_dir / f"{int(row.appid)}_{safe_key}.html").write_text(html, encoding="utf-8")
                record[key] = _result_count(html)
                titles[key] = _top_titles(html)
            except Exception as exc:
                record[key] = 0
                record["external_signal_success"] = False
                record[f"{key}_error"] = str(exc)
            time.sleep(settings.external_request_sleep_seconds)
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
