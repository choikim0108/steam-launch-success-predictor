from __future__ import annotations

import math
from typing import Callable, cast

import pandas as pd

from steam_success.config import SETTINGS
from steam_success.review_analysis import REVIEW_DOMAIN_TERMS, REVIEW_STOP_WORDS, _keywords
from steam_success.reporting import steam_store_url


NOISY_REVIEW_TERMS = {"aaa", "ayy", "es", "nie"}
STRATEGY_TAG_NAMES = {"indie", "free to play", "free-to-play", "early access"}
STRATEGY_TAG_LABELS = {"indie": "Indie", "free to play": "Free to Play", "free-to-play": "Free to Play", "early access": "Early Access"}
NON_GENRE_TERMS = STRATEGY_TAG_NAMES
GENRE_LIKE_TAGS = {
    "action roguelike", "action rpg", "arcade", "base building", "beat 'em up", "card game", "city builder", "crpg", "dating sim", "dungeon crawler", "fps", "fighting", "horror", "jrpg", "metroidvania", "moba", "platformer", "point & click", "puzzle", "racing", "roguelike", "roguelite", "rpg", "rts", "sandbox", "shooter", "simulation", "sports", "strategy", "survival", "tactical", "tower defense", "turn-based strategy", "visual novel"
}
FEATURE_DESCRIPTIONS = {
    "price_final_usd": "출시 가격입니다. 현재 모델에서는 가격대가 유사 게임의 성공 패턴과 얼마나 맞는지 보는 핵심 변수입니다.",
    "supported_language_count": "지원 언어 수입니다. 언어 수가 많을수록 접근 가능한 시장 범위가 넓다는 신호로 해석됩니다.",
    "category_count": "Steam 상점 기능/카테고리 개수입니다. 멀티플레이, 도전과제, 컨트롤러 같은 기능 조합의 풍부함을 나타냅니다.",
    "genre_count": "게임에 연결된 장르 수입니다. 장르 조합의 폭과 포지셔닝 복잡도를 나타냅니다.",
    "is_free": "무료 플레이 여부입니다. 무료 게임은 리뷰 규모와 유입 구조가 유료 게임과 다르게 나타날 수 있습니다.",
    "supports_controller": "컨트롤러 지원 여부입니다. 장르에 따라 접근성과 플레이 경험에 영향을 줍니다.",
    "platform_linux": "Linux 지원 여부입니다. 멀티 플랫폼 지원 범위를 나타냅니다.",
    "supports_achievements": "Steam 도전과제 지원 여부입니다. 반복 플레이와 완성도 신호로 해석될 수 있습니다.",
    "platform_mac": "Mac 지원 여부입니다. 지원 플랫폼 확장성을 나타냅니다.",
    "discount_percent": "할인율입니다. 현재 상점 가격 전략의 영향을 나타냅니다.",
    "has_multiplayer": "멀티플레이/협동 요소 여부입니다. 장르별 시장 기대와 커뮤니티 유지력에 영향을 줍니다.",
    "has_singleplayer": "싱글플레이 지원 여부입니다. 단독 플레이 중심 수요와 관련됩니다.",
    "required_age": "연령 제한입니다. 잠재 이용자 범위와 상점 노출 특성에 영향을 줄 수 있습니다.",
    "platform_windows": "Windows 지원 여부입니다. Steam 기본 시장 접근성의 핵심 조건입니다.",
}


def build_market_insight_payload(dataset: pd.DataFrame, review_topics: pd.DataFrame | None = None, feature_importance: pd.DataFrame | None = None, review_samples: pd.DataFrame | None = None) -> dict[str, object]:
    data = _prepared(dataset)
    topics = review_topics if review_topics is not None else pd.DataFrame()
    importance = feature_importance if feature_importance is not None else pd.DataFrame()
    samples = review_samples if review_samples is not None else pd.DataFrame()
    genres = _ranked_terms(data, "genres")
    tag_column = "steam_tags" if "steam_tags" in data.columns else "categories"
    tags = _ranked_terms(data, tag_column)
    market_trends = [row for row in genres if not _is_strategy_tag(str(row.get("name", "")))]
    review_evidence = _review_evidence(samples)
    return {
        "project": {
            "title": "Steam 시장 트렌드·장르 잠재력 분석 도구",
            "mode": "static_html",
            "model_1": "장르별 상대 기준 기반 성공 분류 모델",
            "model_2": "기획 인사이트 추천 엔진",
        },
        "summary": _summary(data),
        "developer_inputs": _developer_inputs(data, genres, tags),
        "developer_guidance": _developer_guidance(data, genres, tags),
        "semantic_model": _semantic_model(data),
        "market_trends": market_trends,
        "tag_trends": tags,
        "games": _game_catalog(data, review_evidence),
        "similar_games": _similar_games(data, review_evidence),
        "feature_importance": _feature_importance(importance),
        "recommendations": _recommendations(topics),
        "external_data": _external_data(data),
    }


def _prepared(dataset: pd.DataFrame) -> pd.DataFrame:
    data = dataset.copy()
    defaults: dict[str, object] = {
        "genres": "",
        "categories": "",
        "success": 0,
        "predicted_success_probability": 0.0,
        "total_reviews": 0,
        "positive_rate": 0.0,
        "price_final_usd": 0.0,
        "supported_language_count": 0,
        "header_image": "",
        "platform_windows": False,
        "platform_mac": False,
        "platform_linux": False,
        "supports_controller": False,
        "supports_achievements": False,
        "has_multiplayer": False,
        "review_count_30d": 0,
        "review_count_90d": 0,
        "external_attention_score": 0,
        "webzine_mentions": 0,
        "youtube_mentions": 0,
        "blog_mentions": 0,
        "metacritic_score": 0,
        "coming_soon": False,
    }
    for target, source in {"review_count_30d": "reviews_30d", "review_count_90d": "reviews_90d"}.items():
        if target not in data.columns and source in data.columns:
            data[target] = data[source]
    for column, value in defaults.items():
        if column not in data.columns:
            data[column] = value
    return data


def _summary(data: pd.DataFrame) -> dict[str, object]:
    success_count = int(_numeric_series(data, "success").sum()) if not data.empty else 0
    tag_column = "steam_tags" if "steam_tags" in data.columns else "categories"
    return {
        "game_count": int(len(data)),
        "analyzed_tag_count": len(_unique_terms(data, tag_column)),
        "success_count": success_count,
        "success_rate": float(success_count / len(data)) if len(data) else 0.0,
        "average_prediction": _mean(data, "predicted_success_probability"),
        "average_positive_rate": _mean(data, "positive_rate"),
        "total_review_proxy": int(_numeric_series(data, "total_reviews").sum()) if not data.empty else 0,
    }


def _unique_terms(data: pd.DataFrame, column: str) -> set[str]:
    if column not in data.columns:
        return set()
    terms: set[str] = set()
    for value in cast(pd.Series, data[column]).fillna(""):
        terms.update(part for part in _split_terms(str(value)) if part)
    return terms


def _developer_inputs(data: pd.DataFrame, genres: list[dict[str, object]], categories: list[dict[str, object]]) -> dict[str, object]:
    input_genres = list(dict.fromkeys([str(row["name"]) for row in genres if _is_genre_term(str(row["name"]))] + [str(row["name"]) for row in categories if _is_genre_like_tag(str(row["name"]))]))
    genre_names = {name.lower() for name in input_genres}
    strategy_tags = list(dict.fromkeys([_strategy_tag_label(str(row["name"])) for row in genres + categories if _is_strategy_tag(str(row["name"]))]))
    strategy_names = {name.lower() for name in strategy_tags}
    input_tags = [str(row["name"]) for row in categories if str(row["name"]).lower() not in genre_names and _strategy_tag_label(str(row["name"])).lower() not in strategy_names]
    checkbox_fields = _developer_checkbox_fields(data)
    return {
        "genres": input_genres,
        "tags": input_tags,
        "strategy_tags": strategy_tags,
        "numeric_fields": ["price_final_usd", "supported_language_count", "release_month"],
        "checkbox_fields": checkbox_fields,
        "input_groups": [
            _input_group("genres", "메인 장르/세부 장르", input_genres, 12),
            _input_group("strategy_tags", "시장/출시 전략 태그", strategy_tags, 8),
            _input_group("tags", "Steam 태그/기능", input_tags, 12),
            _input_group("checkbox_fields", "상세 기능/카테고리", checkbox_fields, 12, searchable=False),
        ],
    }


def _input_group(key: str, title: str, options: list[str], initial_visible: int, searchable: bool = True) -> dict[str, object]:
    return {"key": key, "title": title, "options": options, "initial_visible": initial_visible, "searchable": searchable, "show_more": len(options) > initial_visible}


def _developer_checkbox_fields(data: pd.DataFrame) -> list[str]:
    fields = ["platform_windows", "platform_mac", "platform_linux", "has_multiplayer", "supports_controller", "supports_achievements"]
    optional = ["has_singleplayer", "is_free", "supports_cloud", "steam_deck_verified", "supports_vr"]
    return fields + [field for field in optional if field in data.columns]


def _developer_guidance(data: pd.DataFrame, genres: list[dict[str, object]], tags: list[dict[str, object]]) -> dict[str, object]:
    eligible_rows = [row for row in genres + tags if not _is_strategy_tag(str(row.get("name", "")))]
    opportunity = _first_trend(eligible_rows, "상승") or _first_trend(eligible_rows, "유지")
    risk = _first_trend(list(reversed(eligible_rows)), "하락")
    average_price = _mean(data, "price_final_usd")
    average_languages = _mean(data, "supported_language_count")
    average_prediction = _mean(data, "predicted_success_probability")
    cards: list[dict[str, object]] = []
    if opportunity:
        cards.append({
            "title": "기회 조합",
            "signal": str(opportunity["name"]),
            "action": f"{opportunity['name']} 방향은 평균 예측 {_float(opportunity['average_prediction']):.1%}입니다. 먼저 작은 범위의 핵심 루프를 만들고 유사 성공작 리뷰를 비교하세요.",
            "evidence": f"표본 {_int(opportunity['game_count'])}개, 성공률 {_float(opportunity['success_rate']):.1%}",
        })
    if risk:
        cards.append({
            "title": "주의 조합",
            "signal": str(risk["name"]),
            "action": f"{risk['name']} 방향은 하락 신호입니다. 차별화 포인트, 리뷰 불만 키워드, 가격 저항을 먼저 검증하세요.",
            "evidence": f"평균 예측 {_float(risk['average_prediction']):.1%}, 성공률 {_float(risk['success_rate']):.1%}",
        })
    cards.append({
        "title": "출시 준비 기준선",
        "signal": f"평균 가격 ${average_price:.2f} · 평균 언어 {average_languages:.1f}개",
        "action": "내 게임 진단 탭에서 가격, 언어 수, 출시월을 직접 넣고 성공/위험 레퍼런스가 어떻게 바뀌는지 확인하세요.",
        "evidence": f"전체 평균 예측 {average_prediction:.1%}",
    })
    return {
        "name": "기획 인사이트 추천 엔진",
        "purpose": "성공확률을 설명 가능한 개발 액션으로 바꾸는 보조 모델",
        "cards": cards,
        "checklist": ["상승 장르/태그에서 핵심 루프 검증", "하락 조합은 차별화와 가격 저항 검증", "성공 레퍼런스 3개와 위험 레퍼런스 3개 리뷰 비교", "출시 전 언어 수와 Steam 기능 지원 범위 결정"],
    }


def _semantic_model(data: pd.DataFrame) -> dict[str, object]:
    return {
        "business_models": _segment_summary(data, _business_model),
        "lifecycles": _segment_summary(data, _lifecycle),
        "production_contexts": _segment_summary(data, _production_context),
        "confidence": _confidence_summary(data),
    }


def _segment_summary(data: pd.DataFrame, classifier: Callable[[dict[str, object]], str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in cast(list[dict[str, object]], data.to_dict(orient="records")):
        label = classifier(row)
        rows.append({"segment": str(label), "success": _int(row.get("success", 0)), "prediction": _float(row.get("predicted_success_probability", 0)), "reviews": _int(row.get("total_reviews", 0))})
    if not rows:
        return []
    grouped = cast(pd.DataFrame, pd.DataFrame(rows).groupby("segment", as_index=False).agg(
        game_count=("success", "size"),
        success_count=("success", "sum"),
        average_prediction=("prediction", "mean"),
        median_reviews=("reviews", "median"),
    ))
    grouped["success_rate"] = grouped["success_count"] / grouped["game_count"]
    ranked = cast(pd.DataFrame, grouped.sort_values(["game_count", "average_prediction"], ascending=False))
    return cast(list[dict[str, object]], ranked.to_dict(orient="records"))


def _confidence_summary(data: pd.DataFrame) -> dict[str, object]:
    games = [_game_confidence(row) for row in cast(list[dict[str, object]], data.to_dict(orient="records"))]
    counts = {label: games.count(label) for label in ["높음", "중간", "낮음"]}
    coverage = _coverage_summary(data)
    return {"label": _dataset_confidence(data, coverage), "counts": counts, "basis": "리뷰 규모, 긍정률, 표본 수, 모집단 coverage, 외부 owners/webzine 보유 여부를 함께 본 보수적 신뢰도", "coverage": coverage}


def _business_model(row: dict[str, object]) -> str:
    terms = _row_terms(row)
    if bool(row.get("is_free", False)) or "free to play" in terms or "free-to-play" in terms:
        return "Free to Play"
    if "in-app purchases" in terms:
        return "Paid + IAP"
    return "Premium/Paid"


def _lifecycle(row: dict[str, object]) -> str:
    terms = _row_terms(row)
    if "early access" in terms:
        return "Early Access"
    if bool(row.get("coming_soon", False)):
        return "Coming Soon"
    return "Released"


def _production_context(row: dict[str, object]) -> str:
    terms = _row_terms(row)
    if "indie" in terms:
        return "Indie"
    return "Publisher-backed/Unknown"


def _row_terms(row: dict[str, object]) -> set[str]:
    text = ", ".join([_text(row.get("genres", "")), _text(row.get("steam_tags", "")), _text(row.get("categories", ""))])
    return {_strategy_tag_key(part) for part in _split_terms(text)}


def _dataset_confidence(data: pd.DataFrame, coverage: dict[str, object] | None = None) -> str:
    coverage_value = _float((coverage or {}).get("sample_coverage", 0))
    coverage_known = _int((coverage or {}).get("release_window_candidates", 0)) > 0
    if len(data) >= 500 and int((_numeric_series(data, "total_reviews") > 0).sum()) >= 200 and coverage_known and coverage_value >= 0.2:
        return "높음"
    if len(data) >= 100:
        return "중간"
    return "낮음"


def _coverage_summary(data: pd.DataFrame) -> dict[str, object]:
    modeled = int(len(data))
    candidates = _coverage_candidate_count(data)
    if candidates <= 0:
        return {"modeled_games": modeled, "release_window_candidates": 0, "sample_coverage": 0.0, "status": "모집단 coverage 데이터 부족"}
    sample_coverage = modeled / candidates if candidates else 0.0
    status = "coverage 낮음" if sample_coverage < 0.2 else "coverage 충분"
    return {"modeled_games": modeled, "release_window_candidates": candidates, "sample_coverage": sample_coverage, "status": status}


def _coverage_candidate_count(data: pd.DataFrame) -> int:
    for column in ["release_window_candidate_count", "release_window_candidates", "population_candidate_count"]:
        if column in data.columns:
            value = _numeric_series(data, column).max()
            return _int(value)
    return 0


def _game_confidence(row: dict[str, object]) -> str:
    reviews = _int(row.get("total_reviews", 0))
    probability = _float(row.get("predicted_success_probability", 0))
    if reviews >= 500 and probability > 0:
        return "높음"
    if reviews >= 100 and probability > 0:
        return "중간"
    return "낮음"


def _first_trend(rows: list[dict[str, object]], trend: str) -> dict[str, object] | None:
    for row in rows:
        if str(row.get("trend", "")) == trend:
            return row
    return None


def _is_genre_term(name: str) -> bool:
    return _strategy_tag_key(name) not in NON_GENRE_TERMS


def _is_strategy_tag(name: str) -> bool:
    return _strategy_tag_key(name) in STRATEGY_TAG_NAMES


def _strategy_tag_label(name: str) -> str:
    return STRATEGY_TAG_LABELS.get(_strategy_tag_key(name), name)


def _strategy_tag_key(name: str) -> str:
    return name.strip().lower().replace("_", " ")


def _is_genre_like_tag(name: str) -> bool:
    return name.strip().lower() in GENRE_LIKE_TAGS


def _ranked_terms(data: pd.DataFrame, column: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if column not in data.columns:
        return rows
    source = cast(pd.DataFrame, data[[column, "success", "predicted_success_probability", "total_reviews", "positive_rate"]])
    for record in cast(list[dict[str, object]], source.to_dict(orient="records")):
        for name in _split_terms(record[column]):
            rows.append({
                "name": name,
                "success": _int(record["success"]),
                "prediction": _float(record["predicted_success_probability"]),
                "reviews": _int(record["total_reviews"]),
                "positive_rate": _float(record["positive_rate"]),
            })
    if not rows:
        return []
    grouped = cast(pd.DataFrame, pd.DataFrame(rows).groupby("name", as_index=False).agg(
        game_count=("success", "size"),
        success_count=("success", "sum"),
        average_prediction=("prediction", "mean"),
        average_reviews=("reviews", "mean"),
        average_positive_rate=("positive_rate", "mean"),
    ))
    grouped["success_rate"] = grouped["success_count"] / grouped["game_count"]
    global_rate = _float(_numeric_series(data, "success").mean()) if len(data) else 0.0
    grouped["smoothed_success_rate"] = (grouped["success_count"] + SETTINGS.criteria_smoothing_alpha * global_rate) / (grouped["game_count"] + SETTINGS.criteria_smoothing_alpha)
    grouped["rank_eligible"] = grouped["game_count"] >= SETTINGS.market_trend_min_sample
    grouped["sample_status"] = grouped["rank_eligible"].map(lambda eligible: "충분" if bool(eligible) else "표본 부족")
    grouped["trend"] = grouped.apply(_trend_label, axis=1)
    ranked = cast(pd.DataFrame, grouped.sort_values(["rank_eligible", "average_prediction", "smoothed_success_rate", "game_count"], ascending=False))
    return cast(list[dict[str, object]], ranked.to_dict(orient="records"))


def _similar_games(data: pd.DataFrame, review_evidence: dict[int, dict[str, object]]) -> dict[str, object]:
    ranked = cast(pd.DataFrame, data.sort_values("predicted_success_probability", ascending=False))
    success_values = _numeric_series(ranked, "success").astype(int)
    success_mask = success_values == 1
    risk_mask = success_values == 0
    success_candidates = cast(pd.DataFrame, ranked[success_mask]).head(8)
    risk_candidates = cast(pd.DataFrame, ranked[risk_mask]).tail(8)
    success_rows = [_game_row(row, review_evidence) for row in cast(list[dict[str, object]], success_candidates.to_dict(orient="records"))]
    risk_rows = [_game_row(row, review_evidence) for row in cast(list[dict[str, object]], risk_candidates.to_dict(orient="records"))]
    success_examples, success_without = _split_review_backed_games(success_rows)
    risk_examples, risk_without = _split_review_backed_games(risk_rows)
    return {
        "success_examples": success_examples,
        "risk_examples": risk_examples,
        "success_without_review_evidence": success_without,
        "risk_without_review_evidence": risk_without,
        "success_average": _group_average(success_candidates),
        "risk_average": _group_average(risk_candidates),
    }


def _split_review_backed_games(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    backed: list[dict[str, object]] = []
    without: list[dict[str, object]] = []
    for row in rows:
        evidence = cast(dict[str, object], row.get("review_evidence", {}))
        if _int(evidence.get("sample_count", 0)) >= SETTINGS.reference_review_min_samples:
            backed.append(row)
        else:
            without.append(row)
    return backed, without


def _game_catalog(data: pd.DataFrame, review_evidence: dict[int, dict[str, object]]) -> list[dict[str, object]]:
    ranked = cast(pd.DataFrame, data.sort_values("predicted_success_probability", ascending=False))
    return [_game_row(row, review_evidence) for row in cast(list[dict[str, object]], ranked.to_dict(orient="records"))]


def _game_row(row: dict[str, object], review_evidence: dict[int, dict[str, object]]) -> dict[str, object]:
    appid = _int(row.get("appid", 0))
    evidence = review_evidence.get(appid, _empty_review_evidence())
    return {
        "appid": appid,
        "name": _text(row.get("name", "")),
        "steam_url": steam_store_url(appid),
        "header_image": _text(row.get("header_image", "")),
        "genres": _text(row.get("genres", "")),
        "steam_tags": _text(row.get("steam_tags", row.get("categories", ""))),
        "platform_windows": bool(row.get("platform_windows", False)),
        "platform_mac": bool(row.get("platform_mac", False)),
        "platform_linux": bool(row.get("platform_linux", False)),
        "platform_count": _platform_count(row),
        "review_count_30d": _int(row.get("review_count_30d", 0)),
        "review_count_90d": _int(row.get("review_count_90d", 0)),
        "review_growth_label": _review_growth_label(row),
        "release_month": _int(row.get("release_month", 0)),
        "price_final_usd": _float(row.get("price_final_usd", 0)),
        "supported_language_count": _int(row.get("supported_language_count", 0)),
        "total_reviews": _int(row.get("total_reviews", 0)),
        "positive_rate": _float(row.get("positive_rate", 0)),
        "predicted_success_probability": _float(row.get("predicted_success_probability", 0)),
        "outcome_label": _outcome_label(_float(row.get("predicted_success_probability", 0))),
        "model_opinion": _model_opinion(row),
        "business_model": _business_model(row),
        "lifecycle": _lifecycle(row),
        "production_context": _production_context(row),
        "confidence": _game_confidence(row),
        "semantic_profile": _semantic_profile(row),
        "review_evidence": evidence,
        "reference_reason": _reference_reason(row, evidence),
    }


def _semantic_profile(row: dict[str, object]) -> dict[str, object]:
    business_value = _business_model(row)
    lifecycle_value = _lifecycle(row)
    production_value = _production_context(row)
    field_confidences = {
        "business_model": _business_model_confidence(row, business_value),
        "lifecycle": _lifecycle_confidence(row, lifecycle_value),
        "production_context": _production_context_confidence(row, production_value),
    }
    values = list(field_confidences.values())
    overall = min(values) if values else 0.0
    return {
        "business_model": {"value": business_value, "confidence": field_confidences["business_model"]},
        "lifecycle": {"value": lifecycle_value, "confidence": field_confidences["lifecycle"]},
        "production_context": {"value": production_value, "confidence": field_confidences["production_context"]},
        "overall_confidence": overall,
        "confidence_band": _confidence_band(overall),
    }


def _business_model_confidence(row: dict[str, object], value: str) -> float:
    terms = _row_terms(row)
    price = _float(row.get("price_final_usd", 0))
    if value == "Free to Play" and (bool(row.get("is_free", False)) or "free to play" in terms):
        return 0.95
    if value == "Paid + IAP" and "in-app purchases" in terms:
        return 0.82
    if value == "Premium/Paid" and price > 0:
        return 0.88
    return 0.55


def _lifecycle_confidence(row: dict[str, object], value: str) -> float:
    terms = _row_terms(row)
    if value == "Early Access" and "early access" in terms:
        return 0.9
    if value == "Coming Soon" and bool(row.get("coming_soon", False)):
        return 0.86
    if value == "Released" and not bool(row.get("coming_soon", False)):
        return 0.75
    return 0.5


def _production_context_confidence(row: dict[str, object], value: str) -> float:
    terms = _row_terms(row)
    if value == "Indie" and "indie" in terms:
        return 0.82
    return 0.45


def _confidence_band(value: float) -> str:
    if value >= 0.8:
        return "높음"
    if value >= 0.6:
        return "중간"
    return "낮음"


def _review_evidence(samples: pd.DataFrame) -> dict[int, dict[str, object]]:
    if samples.empty or "appid" not in samples.columns or "review_text" not in samples.columns:
        return {}
    evidence: dict[int, dict[str, object]] = {}
    for appid, group in samples.groupby("appid"):
        appid_int = _int(appid)
        voted = cast(pd.Series, group["voted_up"]) if "voted_up" in group.columns else pd.Series(dtype=bool)
        positive = cast(pd.DataFrame, group[voted.fillna(False).astype(bool)]) if "voted_up" in group.columns else group.head(0)
        negative = cast(pd.DataFrame, group[~voted.fillna(False).astype(bool)]) if "voted_up" in group.columns else group.head(0)
        playtime = _numeric_series(group, "playtime_hours") if "playtime_hours" in group.columns else pd.Series(dtype=float)
        evidence[appid_int] = {
            "sample_count": int(len(group)),
            "positive_count": int(len(positive)),
            "negative_count": int(len(negative)),
            "average_playtime_hours": float(playtime.mean()) if len(playtime) else 0.0,
            "positive_terms": _keywords(cast(pd.Series, positive["review_text"])) if len(positive) else "데이터 부족",
            "negative_terms": _keywords(cast(pd.Series, negative["review_text"])) if len(negative) else "데이터 부족",
        }
    return evidence


def _empty_review_evidence() -> dict[str, object]:
    return {"sample_count": 0, "positive_count": 0, "negative_count": 0, "average_playtime_hours": 0.0, "positive_terms": "데이터 부족", "negative_terms": "데이터 부족"}


def _reference_reason(row: dict[str, object], evidence: dict[str, object]) -> str:
    probability = _float(row.get("predicted_success_probability", 0))
    reviews = _int(row.get("total_reviews", 0))
    positive_rate = _float(row.get("positive_rate", 0))
    sample_count = _int(evidence.get("sample_count", 0))
    if sample_count:
        return f"선정 근거: 예측 {probability:.1%}, 전체 리뷰 {reviews:,}개, 긍정률 {positive_rate:.1%}. 크롤링 리뷰 {sample_count}개에서 긍정 키워드({evidence.get('positive_terms')})와 부정 키워드({evidence.get('negative_terms')})를 확인했습니다."
    return f"선정 근거: 예측 {probability:.1%}, 전체 리뷰 {reviews:,}개, 긍정률 {positive_rate:.1%}. 이 게임은 리뷰 본문 표본이 없어 모델 지표와 Steam 메타데이터만으로 참고 사례에 포함했습니다."


def _outcome_label(probability: float) -> str:
    if probability >= SETTINGS.outcome_success_probability_threshold:
        return "성공"
    if probability >= SETTINGS.outcome_mid_probability_threshold:
        return "중박"
    return "실패"


def _model_opinion(row: dict[str, object]) -> str:
    probability = _float(row.get("predicted_success_probability", 0))
    reviews = _int(row.get("total_reviews", 0))
    positive_rate = _float(row.get("positive_rate", 0))
    languages = _int(row.get("supported_language_count", 0))
    if probability >= SETTINGS.outcome_success_probability_threshold:
        return f"모델은 높은 긍정률({positive_rate:.1%})과 리뷰 규모({reviews:,}개)를 근거로 이 게임을 성공 패턴에 가깝게 봅니다. 지원 언어 {languages}개도 시장 확장성 신호입니다."
    if probability >= SETTINGS.outcome_mid_probability_threshold:
        return f"모델은 이 게임을 중간권 잠재력으로 봅니다. 긍정률({positive_rate:.1%})은 참고할 만하지만 리뷰 규모({reviews:,}개)와 상점 feature 조합을 함께 확인해야 합니다."
    return f"모델은 이 게임을 위험 사례로 봅니다. 리뷰 규모({reviews:,}개), 긍정률({positive_rate:.1%}), 상점 feature 조합이 성공 표본과 거리가 있습니다."


def _platform_count(row: dict[str, object]) -> int:
    return sum(1 for field in ["platform_windows", "platform_mac", "platform_linux"] if bool(row.get(field, False)))


def _review_growth_label(row: dict[str, object]) -> str:
    count_30d = _int(row.get("review_count_30d", 0))
    count_90d = _int(row.get("review_count_90d", 0))
    if count_30d or count_90d:
        return f"30일 {count_30d:,}개 / 90일 {count_90d:,}개"
    return "리뷰 성장률 데이터 부족"


def _group_average(group: pd.DataFrame) -> dict[str, object]:
    if group.empty:
        return {"sample_size": 0, "price_final_usd": 0.0, "supported_language_count": 0.0, "controller_support_rate": 0.0, "positive_rate": 0.0}
    return {
        "sample_size": int(len(group)),
        "price_final_usd": _mean(group, "price_final_usd"),
        "supported_language_count": _mean(group, "supported_language_count"),
        "controller_support_rate": _bool_rate(group, "supports_controller"),
        "positive_rate": _mean(group, "positive_rate"),
    }


def _feature_importance(data: pd.DataFrame) -> list[dict[str, object]]:
    if data.empty or "feature" not in data.columns or "importance" not in data.columns:
        return []
    rows = []
    source = cast(pd.DataFrame, data[["feature", "importance"]])
    for row in cast(list[dict[str, object]], source.to_dict(orient="records")):
        feature = _text(row.get("feature", ""))
        rows.append({"feature": feature, "importance": _float(row.get("importance", 0)), "importance_description": FEATURE_DESCRIPTIONS.get(feature, "모델 학습 과정에서 성공/실패 구분에 사용된 입력 변수입니다.")})
    return sorted(rows, key=lambda row: float(row["importance"]), reverse=True)[:12]


def _recommendations(topics: pd.DataFrame) -> dict[str, object]:
    cautions = _topic_terms(topics, "negative")
    strengths = _topic_terms(topics, "positive")
    if not cautions:
        cautions = ["최적화", "버그", "반복성", "조작감"]
    if not strengths:
        strengths = ["콘텐츠 완성도", "반복 플레이", "조작감"]
    return {
        "development_cautions": cautions,
        "positioning_strengths": strengths,
        "priority_basis": "유사 성공작/실패작 평균, 장르별 성공률, 리뷰 키워드를 함께 비교",
    }


def _external_data(data: pd.DataFrame) -> dict[str, object]:
    webzine_total = int(_numeric_series(data, "webzine_mentions").sum()) if not data.empty else 0
    webzine_sources = int(_numeric_series(data, "webzine_source_count").max()) if "webzine_source_count" in data.columns and not data.empty else 0
    attention_total = int(_numeric_series(data, "external_attention_score").sum()) if not data.empty else 0
    critic_scores = _numeric_series(data, "metacritic_score") if "metacritic_score" in data.columns else pd.Series(dtype=float)
    critic_count = int((critic_scores > 0).sum())
    owners = _owners_proxy_series(data)
    owners_count = int((owners > 0).sum())
    return {
        "webzine": _availability(webzine_total > 0 or webzine_sources > 0, "웹진 RSS/검색 경로 사용 가능", "데이터 부족으로 웹진 관심도 카드를 비활성화했습니다.", {"mention_count": webzine_total, "source_count": webzine_sources, "attention_score": attention_total}),
        "critic_score": _availability(critic_count > 0, "평점 서비스 데이터 사용 가능", "평점 서비스 매칭 데이터 부족으로 비활성화했습니다.", {"matched_games": critic_count, "average_score": float(critic_scores[critic_scores > 0].mean()) if critic_count else 0.0}),
        "steamspy": _availability(owners_count > 0, "SteamSpy owners proxy 데이터 사용 가능", "SteamSpy owners 데이터가 아직 수집되지 않아 비활성화했습니다.", {"owners_proxy_count": owners_count, "average_owners_proxy": float(owners[owners > 0].mean()) if owners_count else 0.0}),
    }


def _owners_proxy_series(data: pd.DataFrame) -> pd.Series:
    for column in ["steamspy_owners_median", "owners_median", "owners_proxy"]:
        if column in data.columns:
            return _numeric_series(data, column)
    return pd.Series(dtype=float)


def _availability(enabled: bool, ok_reason: str, disabled_reason: str, metrics: dict[str, object]) -> dict[str, object]:
    return {"enabled": enabled, "reason": ok_reason if enabled else disabled_reason, "metrics": metrics}


def _topic_terms(topics: pd.DataFrame, sentiment: str) -> list[str]:
    if topics.empty or "review_sentiment" not in topics.columns or "top_terms" not in topics.columns:
        return []
    matched = cast(pd.DataFrame, topics[topics["review_sentiment"] == sentiment])
    terms: list[str] = []
    for value in cast(pd.Series, matched["top_terms"]).dropna().astype(str).tolist():
        terms.extend([part.strip() for part in value.split(",") if _useful_topic_term(part.strip())])
    return list(dict.fromkeys(terms))[:8]


def _useful_topic_term(term: str) -> bool:
    if not term or term == "데이터 부족":
        return False
    lowered = term.lower()
    if lowered in NOISY_REVIEW_TERMS:
        return False
    parts = lowered.split()
    return bool(parts) and len(lowered) >= 3 and all(part not in REVIEW_STOP_WORDS for part in parts) and any(part in REVIEW_DOMAIN_TERMS for part in parts)


def _trend_label(row: pd.Series) -> str:
    if _int(row["game_count"]) < SETTINGS.market_trend_min_sample:
        return "표본 부족"
    if _float(row["average_prediction"]) >= SETTINGS.market_trend_prediction_threshold and _float(row["success_rate"]) >= SETTINGS.market_trend_success_rate_threshold:
        return "상승"
    if _float(row["average_prediction"]) >= SETTINGS.market_flat_prediction_threshold:
        return "유지"
    return "하락"


def _split_terms(value: object) -> list[str]:
    if _is_missing(value):
        return []
    return [part.strip() for part in str(value).split(",") if part.strip() and part.strip().lower() != "nan"]


def _mean(data: pd.DataFrame, column: str) -> float:
    if data.empty or column not in data.columns:
        return 0.0
    return float(_numeric_series(data, column).mean())


def _numeric_series(data: pd.DataFrame, column: str) -> pd.Series:
    if data.empty or column not in data.columns:
        return pd.Series(dtype=float)
    source = cast(pd.Series, data[column])
    return source.map(_float)


def _bool_rate(data: pd.DataFrame, column: str) -> float:
    if data.empty or column not in data.columns:
        return 0.0
    return float(cast(pd.Series, data[column]).fillna(False).astype(bool).mean())


def _int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if _is_missing(value):
        return 0
    try:
        parsed = float(str(value or 0))
    except (TypeError, ValueError):
        return 0
    if not math.isfinite(parsed):
        return 0
    return int(parsed)


def _float(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    if _is_missing(value):
        return 0.0
    try:
        parsed = float(str(value or 0))
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(parsed):
        return 0.0
    return parsed


def _text(value: object) -> str:
    if _is_missing(value):
        return ""
    return str(value)


def _is_missing(value: object) -> bool:
    try:
        result = pd.isna(value)
    except TypeError:
        return False
    try:
        return bool(result)
    except (TypeError, ValueError):
        return False
