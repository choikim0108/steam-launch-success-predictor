from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd
import requests
from bs4 import BeautifulSoup

from steam_success.collect.steam import CrawlConfig, fetch_appdetails, fetch_review_summaries
from steam_success.config import ProjectPaths, SETTINGS
from steam_success.models.train import train_and_evaluate
from steam_success.preprocess.dataset import build_modeling_dataset


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"


@dataclass(frozen=True)
class TagTrainingConfig:
    games_per_tag: int = 50
    released_through_year: int = 2025
    max_tags: int | None = None
    tag_offset: int = 0
    tag_limit: int | None = None
    pages_per_tag: int = 30
    sleep_seconds: float = 0.20
    country: str = "US"
    language: str = "english"
    sort_by: str = "mixed"
    relative_success_quantile: float = 0.70
    relative_positive_rate_threshold: float = 0.75
    resume_existing: bool = False


def fetch_popular_tags(config: TagTrainingConfig) -> pd.DataFrame:
    url = f"https://store.steampowered.com/tagdata/populartags/{config.language}"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    tags = pd.DataFrame(response.json())
    if config.max_tags is not None:
        tags = tags.head(config.max_tags)
    result = cast(pd.DataFrame, tags.rename(columns={"tagid": "tag_id", "name": "tag_name"}))
    return cast(pd.DataFrame, result.loc[:, ["tag_id", "tag_name"]])


def _load_popular_tags(raw_dir: Path, config: TagTrainingConfig) -> pd.DataFrame:
    cache_path = raw_dir / "steam_popular_tags.csv"
    try:
        tags = fetch_popular_tags(config)
    except Exception:
        if not cache_path.exists():
            raise
        tags = pd.read_csv(cache_path)
    if config.max_tags is not None:
        tags = tags.head(config.max_tags)
    tags.to_csv(cache_path, index=False)
    return cast(pd.DataFrame, tags)


def crawl_tag_appids(tags: pd.DataFrame, raw_dir: Path, config: TagTrainingConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    existing_rows = _existing_tag_rows(raw_dir, config)
    rows: list[dict[str, object]] = cast(list[dict[str, object]], existing_rows.to_dict(orient="records")) if not existing_rows.empty else []
    coverage: list[dict[str, object]] = []
    tag_dir = raw_dir / "tag_search"
    tag_dir.mkdir(parents=True, exist_ok=True)
    for tag in cast(list[dict[str, object]], tags.to_dict(orient="records")):
        tag_id = int(str(tag["tag_id"]))
        tag_name = str(tag["tag_name"])
        seen = _existing_seen(existing_rows, tag_id)
        sort_targets = _sort_targets(config)
        if len(seen) < config.games_per_tag:
            for sort_by, target_count in sort_targets:
                _collect_tag_sort(session, tag_dir, rows, seen, tag_id, tag_name, sort_by, target_count, config)
        coverage.append({"tag_id": tag_id, "tag_name": tag_name, "requested_games": config.games_per_tag, "collected_games": len(seen)})
    tag_rows = _dedupe_tag_rows(pd.DataFrame(rows))
    tag_coverage = pd.DataFrame(coverage)
    tag_rows.to_csv(raw_dir / "steam_tag_search_games.csv", index=False)
    tag_coverage.to_csv(raw_dir / "steam_tag_coverage.csv", index=False)
    return tag_rows, tag_coverage


def train_by_tags(root: Path, config: TagTrainingConfig) -> dict[str, object]:
    paths = ProjectPaths.from_root(root)
    raw_dir = paths.data_raw / "tag_training"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "tag_training_config.json").write_text(json.dumps(config.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    tags = _load_popular_tags(raw_dir, config)
    selected_tags = _tag_batch(tags, config)
    if selected_tags.empty:
        raise RuntimeError(f"No tags selected for offset {config.tag_offset} and limit {config.tag_limit}.")
    tag_rows, tag_coverage = crawl_tag_appids(selected_tags, raw_dir, config)
    if tag_rows.empty:
        raise RuntimeError("No tag search games collected.")
    appids = cast(list[int], tag_rows["appid"].drop_duplicates().astype(int).tolist())
    crawl_config = CrawlConfig(
        max_apps=len(appids),
        pages=config.pages_per_tag,
        sleep_seconds=config.sleep_seconds,
        country=config.country,
        language=config.language,
    )
    details = fetch_appdetails(appids, raw_dir, crawl_config)
    reviews = fetch_review_summaries(appids, raw_dir, crawl_config)
    search = _search_rows_for_model(tag_rows)
    dataset = build_modeling_dataset(search, details, reviews, settings=SETTINGS)
    dataset = cast(pd.DataFrame, dataset.merge(_tag_memberships(tag_rows), on="appid", how="left"))
    dataset = _apply_relative_success(dataset, tag_rows, config)
    dataset.to_csv(paths.data_interim / "tag_training_merged_games.csv", index=False)
    dataset.to_csv(paths.data_processed / "tag_training_modeling_dataset.csv", index=False)
    result = train_and_evaluate(dataset, paths.models, paths.reports, settings=SETTINGS)
    tag_summary = _tag_summary(dataset, tag_rows, tag_coverage)
    tag_summary.to_csv(paths.reports / "tag_training_coverage.csv", index=False)
    (paths.reports / "tag_training_summary.md").write_text(_summary_markdown(config, dataset, tag_summary, result), encoding="utf-8")
    return {"dataset_rows": len(dataset), "unique_appids": len(appids), "tag_count": len(selected_tags), "result": result}


def _tag_batch(tags: pd.DataFrame, config: TagTrainingConfig) -> pd.DataFrame:
    start = max(0, config.tag_offset)
    if config.tag_limit is None:
        return cast(pd.DataFrame, tags.iloc[start:].reset_index(drop=True))
    end = start + max(0, config.tag_limit)
    return cast(pd.DataFrame, tags.iloc[start:end].reset_index(drop=True))


def _existing_tag_rows(raw_dir: Path, config: TagTrainingConfig) -> pd.DataFrame:
    path = raw_dir / "steam_tag_search_games.csv"
    if not config.resume_existing or not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _existing_seen(existing_rows: pd.DataFrame, tag_id: int) -> set[int]:
    if existing_rows.empty or "tag_id" not in existing_rows.columns or "appid" not in existing_rows.columns:
        return set()
    matched = cast(pd.DataFrame, existing_rows[existing_rows["tag_id"].astype(int) == tag_id])
    return set(cast(pd.Series, matched["appid"]).astype(int).tolist())


def _dedupe_tag_rows(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return rows
    keys = [key for key in ["appid", "tag_id", "sample_sort"] if key in rows.columns]
    return cast(pd.DataFrame, rows.drop_duplicates(keys).reset_index(drop=True))


def _search_rows_for_model(tag_rows: pd.DataFrame) -> pd.DataFrame:
    rows = tag_rows.sort_values(["appid", "tag_name"]).drop_duplicates("appid").copy()
    rows["search_page"] = rows["search_page"].fillna(0).astype(int)
    return cast(pd.DataFrame, rows.loc[:, ["appid", "search_name", "search_release_text", "search_price_text", "search_page", "source_url"]])


def _tag_memberships(tag_rows: pd.DataFrame) -> pd.DataFrame:
    grouped = tag_rows.groupby("appid", as_index=False).agg(
        steam_tag_ids=("tag_id", lambda values: ", ".join(str(int(value)) for value in sorted(set(values)))),
        steam_tags=("tag_name", lambda values: ", ".join(sorted(set(str(value) for value in values)))),
        steam_tag_count=("tag_id", "nunique"),
    )
    return cast(pd.DataFrame, grouped)


def _tag_summary(dataset: pd.DataFrame, tag_rows: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    labeled = tag_rows.merge(dataset[["appid", "success", "positive_rate", "total_reviews"]], on="appid", how="inner")
    if labeled.empty:
        summary = coverage.copy()
        summary["trained_games"] = 0
        summary["success_rate"] = 0.0
        return summary
    summary = labeled.groupby(["tag_id", "tag_name"], as_index=False).agg(
        trained_games=("appid", "nunique"),
        success_count=("success", "sum"),
        average_reviews=("total_reviews", "mean"),
        average_positive_rate=("positive_rate", "mean"),
    )
    sort_counts = _sample_sort_counts(tag_rows)
    summary = cast(pd.DataFrame, summary)
    summary["success_rate"] = summary["success_count"] / summary["trained_games"]
    merged = coverage.merge(summary, on=["tag_id", "tag_name"], how="left")
    merged = cast(pd.DataFrame, merged.merge(sort_counts, on=["tag_id", "tag_name"], how="left"))
    return cast(pd.DataFrame, merged.fillna({"trained_games": 0, "success_count": 0, "average_reviews": 0, "average_positive_rate": 0, "success_rate": 0, "sample_breakdown": ""}))


def _sample_sort_counts(tag_rows: pd.DataFrame) -> pd.DataFrame:
    if "sample_sort" not in tag_rows.columns:
        return pd.DataFrame(columns=["tag_id", "tag_name", "sample_breakdown"])
    counts = cast(pd.DataFrame, tag_rows.groupby(["tag_id", "tag_name", "sample_sort"], as_index=False).agg(sample_count=("appid", "nunique")))
    rows: list[dict[str, object]] = []
    for record in cast(list[dict[str, object]], counts.to_dict(orient="records")):
        rows.append({
            "tag_id": int(str(record["tag_id"])),
            "tag_name": str(record["tag_name"]),
            "sample_part": f"{record['sample_sort']}={int(str(record['sample_count']))}",
        })
    parts = pd.DataFrame(rows)
    if parts.empty:
        return pd.DataFrame(columns=["tag_id", "tag_name", "sample_breakdown"])
    return cast(pd.DataFrame, parts.groupby(["tag_id", "tag_name"], as_index=False).agg(sample_breakdown=("sample_part", lambda values: ", ".join(str(value) for value in values))))


def _apply_relative_success(dataset: pd.DataFrame, tag_rows: pd.DataFrame, config: TagTrainingConfig) -> pd.DataFrame:
    data = dataset.copy()
    data["absolute_success"] = data["success"]
    labels: dict[int, int] = {int(str(appid)): 0 for appid in cast(pd.Series, data["appid"]).astype(int).tolist()}
    joined = cast(pd.DataFrame, tag_rows[["appid", "tag_id", "tag_name", "sample_sort"]].merge(data[["appid", "total_reviews", "positive_rate"]], on="appid", how="inner"))
    grouped = cast(pd.DataFrame, joined.groupby(["tag_id", "tag_name"], as_index=False).agg(
        review_threshold=("total_reviews", lambda values: float(pd.Series(values).quantile(config.relative_success_quantile))),
    ))
    threshold_map = {int(str(row["tag_id"])): float(str(row["review_threshold"])) for row in cast(list[dict[str, object]], grouped.to_dict(orient="records"))}
    for row in cast(list[dict[str, object]], joined.to_dict(orient="records")):
        appid = int(str(row["appid"]))
        tag_id = int(str(row["tag_id"]))
        review_count = float(str(row["total_reviews"]))
        positive_rate = float(str(row["positive_rate"]))
        if review_count >= threshold_map.get(tag_id, float("inf")) and positive_rate >= config.relative_positive_rate_threshold:
            labels[appid] = 1
    data["success"] = cast(pd.Series, data["appid"]).astype(int).map(labels).fillna(0).astype(int)
    return data


def _summary_markdown(config: TagTrainingConfig, dataset: pd.DataFrame, tag_summary: pd.DataFrame, result: dict[str, object]) -> str:
    complete = int(cast(Any, (tag_summary["collected_games"] >= config.games_per_tag).sum())) if not tag_summary.empty else 0
    success_count = int(cast(Any, dataset["success"].sum())) if "success" in dataset.columns else 0
    return f"""# Steam 태그별 학습 실행 요약

- 기준: {config.released_through_year}년까지 발매된 게임
- 요청: 태그별 {config.games_per_tag}개 게임
- 처리 태그 수: {len(tag_summary)}
- 태그 배치: offset {config.tag_offset}, limit {config.tag_limit if config.tag_limit is not None else "전체"}, resume {config.resume_existing}
- 요청 수량을 채운 태그 수: {complete}
- 모델 학습 게임 수: {len(dataset)}
- 성공 라벨 게임 수: {success_count}
- 성공 라벨 기준: 태그별 리뷰 수 상위 {(1 - config.relative_success_quantile):.0%} + 긍정률 {config.relative_positive_rate_threshold:.0%} 이상
- 표본 추출 방식: {config.sort_by}
- 선택 모델: {result.get('best_model')}

상세 태그별 커버리지는 `reports/tag_training_coverage.csv`를 확인한다.
"""


def _appid(value: object) -> int | None:
    if not value:
        return None
    try:
        return int(str(value).split(",")[0])
    except ValueError:
        return None


def _text(anchor, selector: str) -> str:
    element = anchor.select_one(selector)
    return element.get_text(strip=True) if element else ""


def _release_year(value: str) -> int | None:
    for fmt in ("%b %d, %Y", "%b %Y", "%Y"):
        try:
            return datetime.strptime(value, fmt).year
        except ValueError:
            continue
    return None


def _sort_targets(config: TagTrainingConfig) -> list[tuple[str, int]]:
    if config.sort_by != "mixed":
        return [(config.sort_by, config.games_per_tag)]
    plan = [
        ("Released_DESC", 0.30),
        ("Reviews_DESC", 0.30),
        ("Price_ASC", 0.20),
        ("Price_DESC", 0.20),
    ]
    counts = [(sort_by, int(config.games_per_tag * ratio)) for sort_by, ratio in plan]
    remainder = config.games_per_tag - sum(count for _, count in counts)
    return [(sort_by, count + (1 if index < remainder else 0)) for index, (sort_by, count) in enumerate(counts)]


def _collect_tag_sort(session: requests.Session, tag_dir: Path, rows: list[dict[str, object]], seen: set[int], tag_id: int, tag_name: str, sort_by: str, target_count: int, config: TagTrainingConfig) -> None:
    start_seen = len(seen)
    try:
        start_page = _first_cutoff_page(session, tag_id, config, sort_by)
    except requests.HTTPError:
        return
    for page in _page_sequence(start_page, config.pages_per_tag, sort_by):
        try:
            response = _search_page(session, tag_id, page, config, sort_by)
        except requests.HTTPError:
            break
        safe_sort = sort_by.lower().replace("_", "")
        (tag_dir / f"tag_{tag_id}_{safe_sort}_page_{page}.html").write_text(response.text, encoding="utf-8")
        soup = BeautifulSoup(response.text, "lxml")
        for anchor in soup.select("a.search_result_row"):
            appid = _appid(anchor.get("data-ds-appid") or anchor.get("data-ds-bundleid"))
            if appid is None or appid in seen:
                continue
            release_text = _text(anchor, "div.search_released")
            release_year = _release_year(release_text)
            if release_year is None or release_year > config.released_through_year:
                continue
            seen.add(appid)
            rows.append({
                "appid": appid,
                "tag_id": tag_id,
                "tag_name": tag_name,
                "search_name": _text(anchor, "span.title"),
                "search_release_text": release_text,
                "search_price_text": _text(anchor, "div.discount_final_price"),
                "search_page": page,
                "sample_sort": sort_by,
                "source_url": response.url,
            })
            if len(seen) - start_seen >= target_count or len(seen) >= config.games_per_tag:
                break
        if len(seen) - start_seen >= target_count or len(seen) >= config.games_per_tag:
            break
        time.sleep(config.sleep_seconds)


def _page_sequence(start_page: int, pages_per_tag: int, sort_by: str) -> list[int]:
    if sort_by == "Released_DESC":
        return list(range(start_page, start_page + pages_per_tag))
    bands = [1, 2, 4, 8, 16, 32, 64, 96, 128, 160, 200, 240]
    return bands[:pages_per_tag]


def _search_page(session: requests.Session, tag_id: int, page: int, config: TagTrainingConfig, sort_by: str) -> requests.Response:
    return _get_with_retry(session, "https://store.steampowered.com/search/", {
        "tags": tag_id,
        "category1": 998,
        "sort_by": sort_by,
        "ignore_preferences": "1",
        "ndl": "1",
        "page": page,
        "cc": config.country,
        "l": config.language,
    })


def _first_cutoff_page(session: requests.Session, tag_id: int, config: TagTrainingConfig, sort_by: str) -> int:
    if sort_by != "Released_DESC":
        return 1
    lower = 1
    upper = 1
    while upper < 512:
        if _page_has_cutoff_year(_search_page(session, tag_id, upper, config, sort_by).text, config.released_through_year):
            break
        lower = upper + 1
        upper *= 2
        time.sleep(config.sleep_seconds)
    if upper >= 512:
        return lower
    while lower < upper:
        middle = (lower + upper) // 2
        if _page_has_cutoff_year(_search_page(session, tag_id, middle, config, sort_by).text, config.released_through_year):
            upper = middle
        else:
            lower = middle + 1
        time.sleep(config.sleep_seconds)
    return lower


def _page_has_cutoff_year(html: str, released_through_year: int) -> bool:
    soup = BeautifulSoup(html, "lxml")
    years = [_release_year(_text(anchor, "div.search_released")) for anchor in soup.select("a.search_result_row")]
    return any(year is not None and year <= released_through_year for year in years)


def _get_with_retry(session: requests.Session, url: str, params: dict[str, str | int]) -> requests.Response:
    delay = 10.0
    for attempt in range(6):
        response = session.get(url, params=params, timeout=30)
        if response.status_code != 429:
            response.raise_for_status()
            return response
        if attempt == 5:
            response.raise_for_status()
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            delay = max(delay, float(retry_after))
        time.sleep(delay)
        delay = min(delay * 1.7, 90.0)
    raise RuntimeError("unreachable retry state")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect 50 games per Steam tag through a release year and train the model.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--games-per-tag", type=int, default=50)
    parser.add_argument("--released-through-year", type=int, default=2025)
    parser.add_argument("--max-tags", type=int, default=None)
    parser.add_argument("--tag-offset", type=int, default=0)
    parser.add_argument("--tag-limit", type=int, default=None)
    parser.add_argument("--pages-per-tag", type=int, default=30)
    parser.add_argument("--sleep-seconds", type=float, default=0.20)
    parser.add_argument("--sort-by", default="mixed")
    parser.add_argument("--relative-success-quantile", type=float, default=0.70)
    parser.add_argument("--relative-positive-rate-threshold", type=float, default=0.75)
    parser.add_argument("--resume-existing", action="store_true")
    args = parser.parse_args()
    result = train_by_tags(
        args.root.resolve(),
        TagTrainingConfig(
            games_per_tag=args.games_per_tag,
            released_through_year=args.released_through_year,
            max_tags=args.max_tags,
            tag_offset=args.tag_offset,
            tag_limit=args.tag_limit,
            pages_per_tag=args.pages_per_tag,
            sleep_seconds=args.sleep_seconds,
            sort_by=args.sort_by,
            relative_success_quantile=args.relative_success_quantile,
            relative_positive_rate_threshold=args.relative_positive_rate_threshold,
            resume_existing=args.resume_existing,
        ),
    )
    print(json.dumps({"dataset_rows": result["dataset_rows"], "unique_appids": result["unique_appids"], "tag_count": result["tag_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
