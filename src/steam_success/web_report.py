from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pandas as pd

from steam_success.market_insight import build_market_insight_payload


SECTION_LABELS = {
    "genre": "장르",
    "category": "상점 카테고리/기능",
    "price_band": "가격대",
    "language_band": "지원 언어 수",
    "platform_count": "지원 플랫폼 수",
    "multiplayer": "멀티플레이 여부",
    "external_attention": "외부 웹 관심도",
}


def _load_table(reports_dir: Path, key: str) -> list[dict[str, object]]:
    path = reports_dir / f"criteria_{key}.csv"
    if not path.exists():
        return []
    table = pd.read_csv(path)
    if table.empty:
        return []
    if "rank_eligible" not in table.columns:
        return cast(list[dict[str, object]], table.head(12).to_dict(orient="records"))
    eligible = table[table["rank_eligible"].map(_truthy)].head(12)
    exploratory = table[~table["rank_eligible"].map(_truthy)].head(12)
    output = cast(pd.DataFrame, pd.concat([eligible, exploratory], ignore_index=True))
    return cast(list[dict[str, object]], output.to_dict(orient="records"))


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


def write_interactive_report(reports_dir: Path, dataset: pd.DataFrame) -> None:
    sections = {key: _load_table(reports_dir, key) for key in SECTION_LABELS}
    metrics_df = pd.read_csv(reports_dir / "model_metrics.csv").sort_values(["f1", "recall", "accuracy"], ascending=False)
    metrics = metrics_df.head(1).to_dict(orient="records")
    conclusions = _build_conclusions(reports_dir, dataset, metrics_df)
    review_topics_frame = _load_review_topics_frame(reports_dir)
    review_topics = review_topics_frame.to_dict(orient="records") if not review_topics_frame.empty else []
    feature_importance = pd.read_csv(reports_dir / "feature_importance.csv") if (reports_dir / "feature_importance.csv").exists() else pd.DataFrame()
    review_samples = pd.read_csv(reports_dir / "review_samples.csv") if (reports_dir / "review_samples.csv").exists() else pd.DataFrame()
    market_payload = build_market_insight_payload(dataset, review_topics_frame, feature_importance, review_samples)
    similar_games = cast(dict[str, object], market_payload.get("similar_games", {})) if isinstance(market_payload.get("similar_games", {}), dict) else {}
    success_references = cast(list[dict[str, object]], similar_games.get("success_examples", []))[:4]
    risk_references = cast(list[dict[str, object]], similar_games.get("risk_examples", []))[:4]
    opportunity = _top_opportunity(market_payload)
    payload = {
        "labels": SECTION_LABELS,
        "sections": sections,
        "summary": {
            "rows": int(len(dataset)),
            "success": len(dataset[dataset["success"] == 1]),
            "failure": len(dataset[dataset["success"] == 0]),
            "metrics": metrics[0] if metrics else {},
            "conclusions": conclusions,
            "opportunity": opportunity,
            "review_topics": review_topics,
            "semantic_model": market_payload.get("semantic_model", {}),
            "external_data": market_payload.get("external_data", {}),
            "reference_games": {"success": success_references, "risk": risk_references},
            "figures": _existing_figures(reports_dir),
        },
    }
    html = HTML_TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
    (reports_dir / "interactive_report.html").write_text(html, encoding="utf-8")


def _top_opportunity(market_payload: dict[str, object]) -> dict[str, object]:
    opportunities = market_payload.get("combination_opportunities", [])
    if not isinstance(opportunities, list) or not opportunities:
        return {}
    first = opportunities[0]
    return cast(dict[str, object], first) if isinstance(first, dict) else {}


def _build_conclusions(reports_dir: Path, dataset: pd.DataFrame, metrics_df: pd.DataFrame) -> dict[str, str]:
    success_count = len(dataset[dataset["success"] == 1])
    success_rate = success_count / len(dataset) if len(dataset) else 0
    best = metrics_df.iloc[0].to_dict() if not metrics_df.empty else {}
    best_model = str(best.get("model", ""))
    best_f1 = float(best.get("f1") or 0)
    best_accuracy = float(best.get("accuracy") or 0)
    genre = _top_criteria(reports_dir, "criteria_genre.csv")
    price = _top_criteria(reports_dir, "criteria_price_band.csv")
    external = _top_criteria(reports_dir, "criteria_external_attention.csv")
    brief = (
        f"현재 표본 {len(dataset)}개 중 성공 기준 충족 게임은 {success_count}개({success_rate:.1%})입니다. "
        f"이번 실행에서는 {best_model}가 F1 {best_f1:.3f}로 가장 높았고, "
        f"상위 장르 경향은 {genre}입니다."
    )
    detail = (
        f"이 모델은 실제 매출이 아니라 리뷰 500개 이상 및 긍정률 80% 이상이라는 운영상 성공 기준을 분류합니다. "
        f"현재 실행에서 {best_model}는 Accuracy {best_accuracy:.3f}, F1 {best_f1:.3f}로 선택됐습니다. "
        f"Random Forest는 비선형 관계와 변수 상호작용을 다룰 수 있어 가격, 언어 수, 카테고리 수, 외부 관심도처럼 성격이 다른 변수를 함께 쓸 때 현재 실험에서는 적합합니다. "
        f"다만 표본 수가 작고 외부 관심도는 검색 결과 proxy이므로, 최종 보고서에서는 '현재 수집 표본에서 가장 성능이 좋았다'고 표현해야 합니다. "
        f"가격대 경향은 {price}, 외부 웹 관심도 경향은 {external}로 요약됩니다."
    )
    return {"brief": brief, "detail": detail}


def _load_review_topics_frame(reports_dir: Path) -> pd.DataFrame:
    path = reports_dir / "review_topic_summary.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _existing_figures(reports_dir: Path) -> list[dict[str, str]]:
    names = ["label_distribution.png", "reviews_vs_positive_rate.png", "feature_importance.png", "analysis_workflow.png", "review_topic_counts.png"]
    result: list[dict[str, str]] = []
    for name in names:
        if (reports_dir / "figures" / name).exists():
            result.append({"src": f"figures/{name}", "name": name})
    return result


def _top_criteria(reports_dir: Path, filename: str) -> str:
    path = reports_dir / filename
    if not path.exists():
        return "데이터 부족"
    table = pd.read_csv(path)
    if table.empty:
        return "데이터 부족"
    if "rank_eligible" in table.columns:
        eligible = table[table["rank_eligible"].map(_truthy)]
        if not eligible.empty:
            table = eligible
    row = table.iloc[0]
    return f"{row['criteria_value']} (성공률 {float(row['success_rate']):.1%}, n={int(row['game_count'])})"


HTML_TEMPLATE = """<!doctype html>
<html lang=\"ko\">
<head>
<meta charset=\"utf-8\">
<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23111827'/%3E%3Ccircle cx='16' cy='16' r='8' fill='%232563eb'/%3E%3C/svg%3E\">
<title>Steam 기획 조합 인사이트 리포트</title>
<style>
body { font-family: Arial, sans-serif; margin: 28px; color: #111827; }
.controls { display: flex; flex-wrap: wrap; gap: 12px; margin: 18px 0; }
.card { border: 1px solid #d1d5db; border-radius: 10px; padding: 16px; margin: 14px 0; }
.bar-row { display: grid; grid-template-columns: 180px 1fr 90px; gap: 10px; align-items: center; margin: 8px 0; }
.bar-bg { background: #e5e7eb; border-radius: 999px; overflow: hidden; height: 18px; }
.bar { background: #2563eb; height: 18px; }
.figure-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }
.figure-grid img { max-width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; }
.topic-table { width: 100%; border-collapse: collapse; }
.topic-table th, .topic-table td { border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; vertical-align: top; }
.small { color: #6b7280; font-size: 0.92em; }
</style>
</head>
<body>
<h1>Steam 기획 조합 인사이트 리포트</h1>
<p>체크박스로 분석 기준을 선택하면 장르, 가격대, 플랫폼, 외부 관심도 등 기준별 관측 성공률 그래프가 표시됩니다.</p>
<div id=\"summary\"></div>
<div class=\"card\"><h2>결론</h2><h3>간략 버전</h3><p id=\"briefConclusion\"></p><h3>상세 버전</h3><p id=\"detailConclusion\"></p></div>
<div class=\"card\" id=\"opportunityAnswer\"></div>
<div class=\"card\"><h2>의미 모델·추천 신뢰도</h2><div id=\"semanticModel\"></div></div>
<div class=\"card\"><h2>외부 데이터 상태</h2><div id=\"externalData\"></div></div>
<div class=\"card\"><h2>관측 성공/실패 근거 사례</h2><div id=\"referenceGames\"></div></div>
<div class=\"card\"><h2>시각화</h2><div class=\"figure-grid\" id=\"figures\"></div></div>
<div class=\"card\"><h2>성장 조합 리뷰 토픽</h2><div id=\"reviewTopics\"></div></div>
<div class=\"controls\" id=\"controls\"></div>
<div id=\"sections\"></div>
<script>
const data = __PAYLOAD__;
const summary = data.summary;
document.getElementById('briefConclusion').textContent = summary.conclusions.brief;
document.getElementById('detailConclusion').textContent = summary.conclusions.detail;
const opportunity = summary.opportunity || {};
document.getElementById('opportunityAnswer').innerHTML = opportunity.combination ? `<h2>성공 가능성이 높은 기획/장르·태그 조합은 뭔가?</h2><p><b>${opportunity.combination}</b> 기획 조합입니다. 기회 점수는 ${(Number(opportunity.opportunity_score || 0) * 100).toFixed(1)}%이고, 관측 성공률은 ${(Number(opportunity.observed_success_rate || 0) * 100).toFixed(1)}%, 근거 표본은 ${Number(opportunity.game_count || 0).toLocaleString()}개입니다.</p><p class="small">${(opportunity.evidence_lines || []).join(' · ')}</p>` : '<h2>성공 가능성이 높은 기획/장르·태그 조합은 뭔가?</h2><p>조합 근거 데이터가 없습니다.</p>';
function pct(value) { return `${(Number(value || 0) * 100).toFixed(1)}%`; }
function num(value) { return Number(value || 0).toLocaleString(); }
function semanticSegments(title, rows) { return `<section><h3>${title}</h3>${(rows || []).slice(0, 4).map(row => `<p class=\"small\">${row.segment}: 표본 ${num(row.game_count)}개 · 모델 보조 평균 ${pct(row.average_prediction)} · 성공률 ${pct(row.success_rate)}</p>`).join('')}</section>`; }
const semantic = summary.semantic_model || {};
const semanticCoverage = semantic.confidence?.coverage || {};
document.getElementById('semanticModel').innerHTML = `<p>전체 추천 신뢰도: ${semantic.confidence?.label || '낮음'} · ${semantic.confidence?.basis || '데이터 보유량 기준'}</p><p class="small">모집단 coverage: ${semanticCoverage.status || '모집단 coverage 데이터 부족'} · 분석 ${num(semanticCoverage.modeled_games || 0)}개 / 후보 ${num(semanticCoverage.release_window_candidates || 0)}개</p>${semanticSegments('비즈니스 모델', semantic.business_models)}${semanticSegments('출시 상태', semantic.lifecycles)}${semanticSegments('제작 맥락', semantic.production_contexts)}`;
const external = summary.external_data || {};
document.getElementById('externalData').innerHTML = Object.entries(external).filter(([key, value]) => value.enabled).map(([key, value]) => `<p><b>${key}</b>: ${value.reason || '데이터 부족'}</p>`).join('') || '<p>표시 가능한 평점 서비스 데이터가 없습니다.</p>';
function gameReasonCard(game) { return `<article class=\"card\"><h3>${game.name}</h3><p class=\"small\">${game.business_model} / ${game.lifecycle} / ${game.production_context} · 신뢰도 ${game.confidence}</p><p>${game.reference_reason}</p><p class=\"small\">항목별 신뢰도: 비즈니스 ${pct(game.semantic_profile?.business_model?.confidence)}, 출시상태 ${pct(game.semantic_profile?.lifecycle?.confidence)}, 제작맥락 ${pct(game.semantic_profile?.production_context?.confidence)}</p><p><a href=\"${game.steam_url}\" target=\"_blank\" rel=\"noreferrer\">Steam 페이지</a></p></article>`; }
const refs = summary.reference_games || {};
document.getElementById('referenceGames').innerHTML = `<h3>성공 참고</h3>${(refs.success || []).map(gameReasonCard).join('') || '<p>성공 참고 데이터가 없습니다.</p>'}<h3>실패/주의 참고</h3>${(refs.risk || []).map(gameReasonCard).join('') || '<p>실패/주의 참고 데이터가 없습니다.</p>'}`;
document.getElementById('figures').innerHTML = (summary.figures || []).map(figure => `<figure><img src=\"${figure.src}\" alt=\"${figure.name}\"><figcaption class=\"small\">${figure.name}</figcaption></figure>`).join('');
const topicRows = summary.review_topics || [];
document.getElementById('reviewTopics').innerHTML = topicRows.length ? `<table class=\"topic-table\"><thead><tr><th>장르</th><th>성공/실패</th><th>긍정/부정</th><th>주요 토픽</th><th>리뷰 수</th></tr></thead><tbody>${topicRows.map(row => `<tr><td>${row.genre}</td><td>${row.game_success}</td><td>${row.review_sentiment}</td><td>${row.top_terms}</td><td>${row.review_count}</td></tr>`).join('')}</tbody></table>` : '<p>리뷰 토픽 데이터가 없습니다.</p>';
document.getElementById('summary').innerHTML = `<div class=\"card\"><b>데이터</b>: ${summary.rows}개 게임, 성공 ${summary.success}개, 비성공 ${summary.failure}개<br><b>모델</b>: ${summary.metrics.model || ''}, F1=${Number(summary.metrics.f1 || 0).toFixed(3)}, Accuracy=${Number(summary.metrics.accuracy || 0).toFixed(3)}<p class=\"small\">F1은 성공/실패 분류의 precision과 recall을 함께 보는 지표입니다.</p></div>`;
const controls = document.getElementById('controls');
Object.entries(data.labels).forEach(([key, label]) => {
  controls.insertAdjacentHTML('beforeend', `<label><input type=\"checkbox\" checked value=\"${key}\" onchange=\"render()\"> ${label}</label>`);
});
function rankEligible(row) {
  return row.rank_eligible === undefined || row.rank_eligible === true || row.rank_eligible === 'True' || row.rank_eligible === 'true';
}
function criteriaBars(rows) {
  return rows.map(row => {
    const rate = Number(row.success_rate || 0);
    const pct = Math.round(rate * 1000) / 10;
    const status = row.sample_status ? ` · ${row.sample_status}` : '';
    return `<div class=\"bar-row\"><div>${row.criteria_value}</div><div class=\"bar-bg\"><div class=\"bar\" style=\"width:${pct}%\"></div></div><div>${pct}%</div></div><div class=\"small\">성공 ${row.success_count} / 전체 ${row.game_count}${status}</div>`;
  }).join('');
}
function sectionHtml(key) {
  const rows = data.sections[key] || [];
  const label = data.labels[key];
  if (!rows.length) return `<div class=\"card\"><h2>${label}</h2><p>표시할 데이터가 없습니다.</p></div>`;
  const eligible = rows.filter(rankEligible);
  const exploratory = rows.filter(row => !rankEligible(row));
  const mainRows = eligible.length ? eligible : rows;
  const exploratoryHtml = exploratory.length ? `<h3>탐색 후보 / 표본 부족</h3>${criteriaBars(exploratory)}` : '';
  return `<div class=\"card\"><h2>${label}</h2>${criteriaBars(mainRows)}${exploratoryHtml}</div>`;
}
function render() {
  const selected = [...document.querySelectorAll('input[type=checkbox]:checked')].map(input => input.value);
  document.getElementById('sections').innerHTML = selected.map(sectionHtml).join('');
}
render();
</script>
</body>
</html>
"""
