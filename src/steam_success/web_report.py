from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


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
    return pd.read_csv(path).head(12).to_dict(orient="records")


def write_interactive_report(reports_dir: Path, dataset: pd.DataFrame) -> None:
    sections = {key: _load_table(reports_dir, key) for key in SECTION_LABELS}
    metrics_df = pd.read_csv(reports_dir / "model_metrics.csv").sort_values(["f1", "recall", "accuracy"], ascending=False)
    metrics = metrics_df.head(1).to_dict(orient="records")
    conclusions = _build_conclusions(dataset, metrics_df)
    payload = {
        "labels": SECTION_LABELS,
        "sections": sections,
        "summary": {
            "rows": int(len(dataset)),
            "success": int(dataset["success"].sum()),
            "failure": int((dataset["success"] == 0).sum()),
            "metrics": metrics[0] if metrics else {},
            "conclusions": conclusions,
        },
    }
    html = HTML_TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
    (reports_dir / "interactive_report.html").write_text(html, encoding="utf-8")


def _build_conclusions(dataset: pd.DataFrame, metrics_df: pd.DataFrame) -> dict[str, str]:
    success_count = int(dataset["success"].sum())
    failure_count = int((dataset["success"] == 0).sum())
    success_rate = success_count / len(dataset) if len(dataset) else 0
    best = metrics_df.iloc[0].to_dict() if not metrics_df.empty else {}
    best_model = str(best.get("model", ""))
    best_f1 = float(best.get("f1") or 0)
    best_accuracy = float(best.get("accuracy") or 0)
    genre = _top_criteria("criteria_genre.csv")
    price = _top_criteria("criteria_price_band.csv")
    external = _top_criteria("criteria_external_attention.csv")
    brief = (
        f"현재 표본 {len(dataset)}개 중 성공 기준 충족 게임은 {success_count}개({success_rate:.1%})입니다. "
        f"이번 실행에서는 {best_model}가 F1 {best_f1:.3f}로 가장 높았고, "
        f"상위 장르 경향은 {genre}입니다."
    )
    detail = (
        f"이 모델은 실제 매출이 아니라 리뷰 500개 이상 및 긍정률 80% 이상이라는 운영상 성공 기준을 예측합니다. "
        f"현재 실행에서 {best_model}는 Accuracy {best_accuracy:.3f}, F1 {best_f1:.3f}로 선택됐습니다. "
        f"Random Forest는 비선형 관계와 변수 상호작용을 다룰 수 있어 가격, 언어 수, 카테고리 수, 외부 관심도처럼 성격이 다른 변수를 함께 쓸 때 현재 실험에서는 적합합니다. "
        f"다만 표본 수가 작고 외부 관심도는 검색 결과 proxy이므로, 최종 보고서에서는 '현재 수집 표본에서 가장 성능이 좋았다'고 표현해야 합니다. "
        f"가격대 경향은 {price}, 외부 웹 관심도 경향은 {external}로 요약됩니다."
    )
    return {"brief": brief, "detail": detail}


def _top_criteria(filename: str) -> str:
    path = Path("reports") / filename
    if not path.exists():
        return "데이터 부족"
    table = pd.read_csv(path)
    if table.empty:
        return "데이터 부족"
    row = table.iloc[0]
    return f"{row['criteria_value']} (성공률 {float(row['success_rate']):.1%}, n={int(row['game_count'])})"


HTML_TEMPLATE = """<!doctype html>
<html lang=\"ko\">
<head>
<meta charset=\"utf-8\">
<title>Steam 성공 예측 인터랙티브 리포트</title>
<style>
body { font-family: Arial, sans-serif; margin: 28px; color: #111827; }
.controls { display: flex; flex-wrap: wrap; gap: 12px; margin: 18px 0; }
.card { border: 1px solid #d1d5db; border-radius: 10px; padding: 16px; margin: 14px 0; }
.bar-row { display: grid; grid-template-columns: 180px 1fr 90px; gap: 10px; align-items: center; margin: 8px 0; }
.bar-bg { background: #e5e7eb; border-radius: 999px; overflow: hidden; height: 18px; }
.bar { background: #2563eb; height: 18px; }
.small { color: #6b7280; font-size: 0.92em; }
</style>
</head>
<body>
<h1>Steam 출시 성공 예측 인터랙티브 리포트</h1>
<p>체크박스로 분석 기준을 선택하면 장르, 가격대, 플랫폼, 외부 관심도 등 기준별 성공률 그래프가 표시됩니다.</p>
<div id=\"summary\"></div>
<div class=\"card\"><h2>결론</h2><h3>간략 버전</h3><p id=\"briefConclusion\"></p><h3>상세 버전</h3><p id=\"detailConclusion\"></p></div>
<div class=\"controls\" id=\"controls\"></div>
<div id=\"sections\"></div>
<script>
const data = __PAYLOAD__;
const summary = data.summary;
document.getElementById('briefConclusion').textContent = summary.conclusions.brief;
document.getElementById('detailConclusion').textContent = summary.conclusions.detail;
document.getElementById('summary').innerHTML = `<div class=\"card\"><b>데이터</b>: ${summary.rows}개 게임, 성공 ${summary.success}개, 비성공 ${summary.failure}개<br><b>모델</b>: ${summary.metrics.model || ''}, F1=${Number(summary.metrics.f1 || 0).toFixed(3)}, Accuracy=${Number(summary.metrics.accuracy || 0).toFixed(3)}<p class=\"small\">F1은 성공/실패 예측의 precision과 recall을 함께 보는 지표입니다.</p></div>`;
const controls = document.getElementById('controls');
Object.entries(data.labels).forEach(([key, label]) => {
  controls.insertAdjacentHTML('beforeend', `<label><input type=\"checkbox\" checked value=\"${key}\" onchange=\"render()\"> ${label}</label>`);
});
function sectionHtml(key) {
  const rows = data.sections[key] || [];
  const label = data.labels[key];
  if (!rows.length) return `<div class=\"card\"><h2>${label}</h2><p>표시할 데이터가 없습니다.</p></div>`;
  const bars = rows.map(row => {
    const rate = Number(row.success_rate || 0);
    const pct = Math.round(rate * 1000) / 10;
    return `<div class=\"bar-row\"><div>${row.criteria_value}</div><div class=\"bar-bg\"><div class=\"bar\" style=\"width:${pct}%\"></div></div><div>${pct}%</div></div><div class=\"small\">성공 ${row.success_count} / 전체 ${row.game_count}</div>`;
  }).join('');
  return `<div class=\"card\"><h2>${label}</h2>${bars}</div>`;
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
