from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from steam_success.config import SETTINGS
from steam_success.market_insight import build_market_insight_payload


def write_market_insight_site(reports_dir: Path, dataset: pd.DataFrame, review_topics: pd.DataFrame | None = None, feature_importance: pd.DataFrame | None = None, review_samples: pd.DataFrame | None = None) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    if review_samples is None and (reports_dir / "review_samples.csv").exists():
        review_samples = pd.read_csv(reports_dir / "review_samples.csv")
    payload = build_market_insight_payload(dataset, review_topics, feature_importance, review_samples)
    data_json = _script_json(payload)
    output = reports_dir / "market_insight_site.html"
    html = (
        HTML_TEMPLATE.replace("__PAYLOAD__", data_json)
        .replace("__SUCCESS_THRESHOLD__", f"{SETTINGS.outcome_success_probability_threshold:.0%}")
        .replace("__MID_THRESHOLD__", f"{SETTINGS.outcome_mid_probability_threshold:.0%}")
    )
    output.write_text(html, encoding="utf-8")
    return output


def _script_json(payload: dict[str, object]) -> str:
    data = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    return data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


HTML_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230d1324'/%3E%3Ccircle cx='16' cy='16' r='8' fill='%2360a5fa'/%3E%3C/svg%3E">
<title>Steam 시장 트렌드·장르 잠재력 분석 도구</title>
<style>
:root { --bg:#0d1324; --ink:#e8edf7; --muted:#94a3b8; --card:rgba(20,31,55,.82); --line:rgba(148,163,184,.22); --blue:#60a5fa; --green:#34d399; --red:#fb7185; --yellow:#fbbf24; --violet:#a78bfa; --rose:#f472b6; }
* { box-sizing:border-box; }
body { margin:0; background:radial-gradient(circle at 15% 5%, rgba(96,165,250,.22), transparent 30%), radial-gradient(circle at 80% 0%, rgba(244,114,182,.16), transparent 28%), var(--bg); color:var(--ink); font-family:Georgia,"Noto Serif KR",serif; line-height:1.55; }
header { padding:52px 32px 38px; border-bottom:1px solid var(--line); }
header p { max-width:1040px; color:#cbd5e1; }
main { width:min(1180px, calc(100% - 32px)); margin:22px auto 44px; }
.grid { display:grid; gap:14px; }
.cols-2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.cols-3 { grid-template-columns:repeat(3,minmax(0,1fr)); }
.card { background:linear-gradient(180deg, rgba(30,41,70,.9), rgba(15,23,42,.78)); border:1px solid var(--line); border-radius:22px; padding:20px; margin:14px 0; box-shadow:0 18px 50px rgba(0,0,0,.24); backdrop-filter:blur(12px); }
.muted { color:var(--muted); }
.metric { font-size:28px; font-weight:700; display:block; }
.pill { display:inline-block; padding:6px 10px; border-radius:999px; background:rgba(96,165,250,.16); margin:4px; font-size:13px; }
.disabled { opacity:.68; border-style:dashed; }
.enabled { border-left:5px solid var(--green); }
.warning { color:var(--yellow); font-weight:700; }
.risk { color:var(--red); font-weight:700; }
label { display:inline-block; margin:5px 10px 5px 0; }
input[type="number"] { width:86px; padding:7px; border:1px solid var(--line); border-radius:10px; background:#0f172a; color:var(--ink); }
table { width:100%; border-collapse:collapse; }
th,td { border-bottom:1px solid var(--line); padding:8px; text-align:left; vertical-align:top; }
a { color:var(--blue); }
.bar-bg { height:16px; border-radius:999px; background:#e5e7eb; overflow:hidden; }
.bar { height:16px; background:var(--blue); }
.chip-row { display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 14px; }
.impact-chip { border:1px solid var(--line); border-radius:999px; padding:9px 13px; background:rgba(15,23,42,.78); color:var(--ink); cursor:pointer; transition:.18s ease; }
.impact-chip:hover { transform:translateY(-1px); border-color:var(--blue); }
.impact-chip.active { background:linear-gradient(135deg,var(--blue),var(--violet)); color:#06111f; font-weight:700; }
.impact-chip:disabled { cursor:not-allowed; opacity:.38; transform:none; }
.game-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }
.game-card { text-align:left; border:1px solid var(--line); background:rgba(15,23,42,.72); color:var(--ink); border-radius:16px; padding:14px; cursor:pointer; min-height:150px; }
.game-card:hover { border-color:var(--green); transform:translateY(-2px); }
.label-success { color:var(--green); font-weight:800; }
.label-mid { color:var(--yellow); font-weight:800; }
.label-fail { color:var(--red); font-weight:800; }
.trend-up { color:var(--green); font-weight:800; }
.trend-flat { color:var(--yellow); font-weight:800; }
.trend-down { color:var(--red); font-weight:800; }
.scenario-card { border:1px solid var(--line); border-radius:18px; padding:14px; background:rgba(96,165,250,.1); }
.insight-card { border-left:5px solid var(--green); }
.combo-card { border-left:5px solid var(--violet); }
.checklist li { margin:7px 0; }
.criteria-list { display:grid; gap:8px; padding-left:18px; }
.modal { position:fixed; inset:0; display:none; align-items:center; justify-content:center; background:rgba(2,6,23,.72); padding:18px; z-index:10; }
.modal.open { display:flex; }
.modal-panel { width:min(720px,100%); background:#111827; border:1px solid var(--line); border-radius:22px; padding:22px; box-shadow:0 28px 80px rgba(0,0,0,.45); }
.modal-actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; }
.button-link, .ghost-button { border:1px solid var(--line); border-radius:999px; padding:10px 14px; background:rgba(96,165,250,.14); color:var(--ink); text-decoration:none; cursor:pointer; }
.tab-shell { position:sticky; top:0; z-index:3; display:flex; justify-content:center; margin:0 0 22px; padding:14px 0; background:rgba(13,19,36,.92); backdrop-filter:blur(10px); }
.tabs { display:flex; flex-wrap:wrap; justify-content:center; gap:8px; padding:8px; background:rgba(15,23,42,.88); border:1px solid var(--line); border-radius:999px; box-shadow:0 16px 36px rgba(0,0,0,.2); }
.tab-button { border:1px solid transparent; border-radius:999px; padding:10px 16px; background:transparent; color:var(--muted); cursor:pointer; }
.tab-button.active { background:linear-gradient(135deg,var(--blue),var(--violet)); color:#06111f; font-weight:800; }
.tab-panel { display:none; }
.tab-panel.active { display:block; }
.game-image { width:100%; aspect-ratio:2.18/1; object-fit:cover; border-radius:12px; margin-bottom:10px; background:rgba(148,163,184,.16); }
.reference-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:14px; }
@media (max-width:900px) { .cols-2,.cols-3 { grid-template-columns:1fr; } }
</style>
</head>
<body>
<header>
<h1>Steam 시장 트렌드·장르 잠재력 분석 도구</h1>
<p>수집·학습한 Steam 데이터와 외부 지표를 기반으로 게임 개발자가 선택한 장르와 태그의 시장성, 성공 가능성, 개발 주의점을 확인하는 발표용 정적 HTML 웹사이트입니다.</p>
</header>
<main>
<div class="tab-shell"><nav class="tabs" aria-label="시장 인사이트 탭"><button class="tab-button active" data-tab="overview" type="button">시장 스냅샷</button><button class="tab-button" data-tab="planner" type="button">내 게임 진단</button><button class="tab-button" data-tab="risks" type="button">성공 레퍼런스</button><button class="tab-button" data-tab="evidence" type="button">판단 기준</button></nav></div>
<section class="tab-panel active" id="tab-overview"><div class="scenario-card"><b>이 탭의 쓰임</b><p class="muted">개발자 시나리오: 먼저 전체 시장 규모, 성공 표본 비율, 장르/태그 방향을 보고 기획 후보를 좁힙니다.</p></div><section class="grid cols-3" id="summary"></section><section class="card"><h2>기획 인사이트 추천 엔진</h2><p class="muted" id="guidancePurpose"></p><div class="grid cols-3" id="guidanceCards"></div><h3>출시 전 체크리스트</h3><ul class="checklist" id="guidanceChecklist"></ul></section><section class="card"><h2>의미 모델·추천 신뢰도</h2><div id="semanticModel"></div></section><section class="grid cols-2"><div class="card"><h2>장르 트렌드</h2><div id="genreTrends"></div></div><div class="card"><h2>태그/기능 트렌드</h2><div id="tagTrends"></div></div></section></section>
<section class="tab-panel" id="tab-planner"><div class="scenario-card"><b>이 탭의 쓰임</b><p class="muted">개발자 시나리오: 만들려는 장르/태그를 선택하고, 성공 참고 게임과 실패/주의 참고 게임을 같이 비교합니다.</p></div><section class="card"><h2>내 게임 기획 입력</h2><p class="muted">선택 전에는 전체 시장 평균을 기준으로 표시합니다. 가격/언어 수/출시월은 일부러 비워두어 사용자가 직접 입력한 값만 반영합니다.</p><div id="inputs"></div><div id="estimate" class="card"></div><div id="tagComboRecommendations" class="card combo-card"></div></section><section class="card"><h2>선택 조건 기반 참고 게임</h2><div id="selectedGames"></div></section></section>
<section class="tab-panel" id="tab-evidence"><div class="scenario-card"><b>이 탭의 쓰임</b><p class="muted">개발자 시나리오: 모델이 어떤 요소를 중요하게 봤는지 확인하고 가격·언어·플랫폼 전략을 조정합니다.</p></div><section class="grid cols-2"><div class="card"><h2>모델 근거 feature importance</h2><div id="importance"></div></div><div class="card"><h2>성공/중박/실패 기준</h2><ul class="criteria-list"><li>성공: __SUCCESS_THRESHOLD__ 이상</li><li>중박: __MID_THRESHOLD__ 이상 __SUCCESS_THRESHOLD__ 미만</li><li>실패: __MID_THRESHOLD__ 미만</li></ul><div id="comparison"></div></div></section></section>
<section class="tab-panel" id="tab-risks"><div class="scenario-card"><b>이 탭의 쓰임</b><p class="muted">개발자 시나리오: 비슷한 실패 사례와 부정 리뷰 키워드를 보고 출시 전 리스크 체크리스트를 만듭니다.</p></div><section class="grid cols-2"><div class="card"><h2>유사 성공작</h2><div id="successGames"></div></div><div class="card"><h2>유사 실패/위험 사례</h2><div id="riskGames"></div></div></section><section class="grid cols-2"><div class="card"><h2>개발 주의점</h2><div id="cautions"></div></div><div class="card"><h2>외부 데이터 상태</h2><div id="external"></div></div></section></section>
</main>
<div id="gameModal" class="modal" role="dialog" aria-modal="true" aria-labelledby="gameDetailTitle"><div class="modal-panel"><div id="gameDetail"></div><div class="modal-actions"><a id="steamDetailLink" class="button-link" target="_blank" rel="noreferrer">Steam 페이지 열기</a><button class="ghost-button" onclick="closeGameDetail()">닫기</button></div></div></div>
<script id="market-data" type="application/json">__PAYLOAD__</script>
<script>
const payload = JSON.parse(document.getElementById('market-data').textContent);
const selectedState = { genres:new Set(), tags:new Set() };
const pct = value => `${(Number(value || 0) * 100).toFixed(1)}%`;
const num = value => Number(value || 0).toLocaleString();
function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined && text !== null) element.textContent = String(text);
  return element;
}
function add(parent, child) { parent.appendChild(child); return child; }
function renderSummary() {
  const s = payload.summary;
  const target = document.getElementById('summary');
  clear(target);
  [
    ['분석 게임 수', `${num(s.game_count)}개`, '수집·정제 후 HTML에 반영된 표본'],
    ['분석 태그 수', `${num(s.analyzed_tag_count)}개`, 'Steam 태그/기능 기반 세부 시장 축'],
    ['성공 표본 비율', pct(s.success_rate), '장르별 상대 성공 기준 기반'],
    ['평균 예측 확률', pct(s.average_prediction), '모델 1 결과 평균']
  ].forEach(([title, metric, desc]) => {
    const card = add(target, node('div', '', 'card'));
    add(card, node('span', metric, 'metric'));
    add(card, node('b', title));
    add(card, node('p', desc, 'muted'));
  });
}
function renderGuidance() {
  const guidance = payload.developer_guidance || {};
  const purpose = document.getElementById('guidancePurpose');
  purpose.textContent = guidance.purpose || '성공확률을 개발 액션으로 바꾸는 보조 모델입니다.';
  const cards = document.getElementById('guidanceCards');
  clear(cards);
  (guidance.cards || []).forEach(item => {
    const card = add(cards, node('div', '', 'card insight-card'));
    add(card, node('b', item.title));
    add(card, node('span', item.signal, 'metric'));
    add(card, node('p', item.action));
    add(card, node('p', item.evidence, 'muted'));
  });
  const checklist = document.getElementById('guidanceChecklist');
  clear(checklist);
  (guidance.checklist || []).forEach(item => add(checklist, node('li', item)));
}
function renderSemanticModel() {
  const target = document.getElementById('semanticModel');
  clear(target);
  const semantic = payload.semantic_model || {};
  add(target, node('p', `전체 추천 신뢰도: ${semantic.confidence?.label || '낮음'} · ${semantic.confidence?.basis || '데이터 보유량 기준'}`, 'muted'));
  const coverage = semantic.confidence?.coverage || {};
  add(target, node('p', `모집단 coverage: ${coverage.status || '모집단 coverage 데이터 부족'} · 분석 ${num(coverage.modeled_games || 0)}개 / 후보 ${num(coverage.release_window_candidates || 0)}개`, 'muted'));
  const layout = add(target, node('div', '', 'grid cols-3'));
  [['비즈니스 모델', semantic.business_models], ['출시 상태', semantic.lifecycles], ['제작 맥락', semantic.production_contexts]].forEach(([title, rows]) => {
    const card = add(layout, node('div', '', 'card'));
    add(card, node('b', title));
    (rows || []).slice(0, 4).forEach(row => add(card, node('p', `${row.segment}: 표본 ${num(row.game_count)}개 · 평균 예측 ${pct(row.average_prediction)} · 성공률 ${pct(row.success_rate)}`, 'muted')));
  });
}
function heading(parent, text) { add(parent, node('h3', text)); }
function renderImpactChips(parent, type, values) {
  const row = add(parent, node('div', '', 'chip-row'));
  values.forEach(value => {
    const button = add(row, node('button', value, 'impact-chip'));
    button.type = 'button';
    button.dataset.value = value;
    button.dataset.kind = type;
    button.setAttribute('data-impact-disabled', 'false');
    button.onclick = () => toggleTerm(type, value);
  });
}
function numeric(parent, id, labelText, value, min, max) {
  const label = add(parent, node('label'));
  label.appendChild(document.createTextNode(`${labelText} `));
  const input = add(label, node('input'));
  input.type = 'number';
  input.id = id;
  input.value = value;
  if (min !== undefined) input.min = min;
  if (max !== undefined) input.max = max;
  input.onchange = updateInterface;
}
function renderInputs() {
  const inputs = payload.developer_inputs;
  const target = document.getElementById('inputs');
  clear(target);
  (inputs.input_groups || [
    {key:'genres', title:'메인 장르/세부 장르', options:inputs.genres || [], initial_visible:12, searchable:true, show_more:true},
    {key:'strategy_tags', title:'시장/출시 전략 태그', options:inputs.strategy_tags || [], initial_visible:8, searchable:true, show_more:true},
    {key:'tags', title:'Steam 태그/기능', options:inputs.tags || [], initial_visible:12, searchable:true, show_more:true}
  ]).filter(group => group.key !== 'checkbox_fields').forEach(renderInputGroup);
  heading(target, '상세 기획');
  const optimizeButton = add(target, node('button', '선택 조건 최적화', 'ghost-button'));
  optimizeButton.id = 'maximizePlanButton';
  optimizeButton.type = 'button';
  optimizeButton.onclick = optimizePlanningInputs;
  numeric(target, 'price', '가격', '');
  numeric(target, 'languages', '언어 수', '');
  numeric(target, 'month', '출시월', '', '1', '12');
  const labels = {platform_windows:'Windows', platform_mac:'Mac', platform_linux:'Linux', has_multiplayer:'멀티플레이', supports_controller:'컨트롤러', supports_achievements:'도전과제', has_singleplayer:'싱글플레이', is_free:'무료 플레이', supports_cloud:'Steam Cloud', steam_deck_verified:'Steam Deck', supports_vr:'VR'};
  (inputs.checkbox_fields || []).forEach(field => checkbox(target, field, 'true', labels[field] || field));
}
function renderInputGroup(group) {
  const target = document.getElementById('inputs');
  heading(target, group.title);
  const wrapper = add(target, node('div', '', 'input-group'));
  wrapper.dataset.inputGroup = group.key;
  if (group.searchable) {
    const search = add(wrapper, node('input'));
    search.type = 'search';
    search.placeholder = `${group.title} 검색`;
    search.oninput = () => filterInputGroup(group.key, search.value);
  }
  const options = group.options || [];
  const visible = Number(group.initial_visible || options.length);
  renderImpactChips(wrapper, group.key, options.slice(0, visible));
  if (!options.length) add(wrapper, node('p', `${group.title} 데이터 부족`, 'muted'));
  if (group.show_more) {
    const button = add(wrapper, node('button', '더보기', 'ghost-button'));
    button.type = 'button';
    button.onclick = () => showMoreInputGroup(group.key);
  }
}
function filterInputGroup(key, query) {
  const group = (payload.developer_inputs.input_groups || []).find(item => item.key === key);
  const wrapper = document.querySelector(`[data-input-group="${key}"]`);
  if (!group || !wrapper) return;
  const row = wrapper.querySelector('.chip-row');
  if (row) row.remove();
  const matched = (group.options || []).filter(value => String(value).toLowerCase().includes(String(query || '').toLowerCase()));
  renderImpactChips(wrapper, key, matched.slice(0, Number(group.initial_visible || matched.length)));
  updateChips(probabilityFor(selectedTerms()));
}
function showMoreInputGroup(key) {
  const group = (payload.developer_inputs.input_groups || []).find(item => item.key === key);
  const wrapper = document.querySelector(`[data-input-group="${key}"]`);
  if (!group || !wrapper) return;
  const row = wrapper.querySelector('.chip-row');
  if (row) row.remove();
  renderImpactChips(wrapper, key, group.options || []);
  updateChips(probabilityFor(selectedTerms()));
}
function checkbox(parent, name, value, labelText) {
  const label = add(parent, node('label'));
  const input = add(label, node('input'));
  input.type = 'checkbox'; input.name = name; input.value = value; input.onchange = updateInterface;
  label.appendChild(document.createTextNode(` ${labelText}`));
}
function toggleTerm(type, value) {
  const set = selectedSet(type);
  if (set.has(value)) set.delete(value); else set.add(value);
  updateInterface();
}
function selectedSet(type) {
  if (!selectedState[type]) selectedState[type] = new Set();
  return selectedState[type];
}
function gameTerms(game) {
  return [...new Set(`${game.genres || ''}, ${game.steam_tags || ''}`.split(',').map(v => v.trim()).filter(Boolean))];
}
function selectedTerms(extraType, extraValue) {
  const terms = [...selectedSet('genres'), ...selectedSet('strategy_tags'), ...selectedSet('tags')];
  if (extraType && extraValue) terms.push(extraValue);
  return terms;
}
function matchingGames(terms) {
  const games = payload.games || [];
  if (!terms.length) return games;
  return games.filter(game => terms.every(term => gameTerms(game).includes(term)));
}
function termsFrom(value) {
  return `${value || ''}`.split(',').map(v => v.trim()).filter(Boolean);
}
function gameGenreTerms(game) {
  return termsFrom(game.genres);
}
function gameTagTerms(game) {
  const genres = new Set(gameGenreTerms(game));
  return [...new Set(termsFrom(game.steam_tags).filter(tag => !genres.has(tag)))];
}
function gameHasGenreSelection(game, genre) {
  return gameGenreTerms(game).includes(genre) || gameTagTerms(game).includes(genre);
}
function tagComboCandidates() {
  const genres = [...selectedState.genres];
  if (!genres.length) return [];
  const games = (payload.games || []).filter(game => genres.every(genre => gameHasGenreSelection(game, genre)));
  const combos = new Map();
  games.forEach(game => {
    const tags = gameTagTerms(game).slice(0, 8);
    const candidates = tags.map(tag => [tag]);
    for (let i = 0; i < tags.length; i += 1) {
      for (let j = i + 1; j < tags.length; j += 1) candidates.push([tags[i], tags[j]]);
    }
    candidates.forEach(combo => {
      const key = combo.join(' + ');
      const previous = combos.get(key) || {combo:key, sample:0, probabilitySum:0, successSum:0};
      previous.sample += 1;
      previous.probabilitySum += Number(game.predicted_success_probability || 0);
      previous.successSum += game.outcome_label === '성공' ? 1 : 0;
      combos.set(key, previous);
    });
  });
  return Array.from(combos.values())
    .filter(row => row.sample >= 2)
    .map(row => ({combo:row.combo, sample:row.sample, probability:row.probabilitySum / row.sample, successRate:row.successSum / row.sample}))
    .sort((a, b) => b.probability - a.probability || b.sample - a.sample)
    .slice(0, 8);
}
function optimizePlanningInputs() {
  const baseTerms = selectedTerms();
  const candidates = matchingGames(baseTerms).length ? matchingGames(baseTerms) : (payload.games || []);
  const ranked = candidates.slice().sort((a, b) => Number(b.predicted_success_probability || 0) - Number(a.predicted_success_probability || 0)).slice(0, 12);
  if (!ranked.length) return;
  const average = (field) => ranked.reduce((sum, game) => sum + Number(game[field] || 0), 0) / ranked.length;
  document.getElementById('price').value = average('price_final_usd').toFixed(2);
  document.getElementById('languages').value = Math.max(1, Math.round(average('supported_language_count')));
  const month = Math.round(average('release_month')) || 10;
  document.getElementById('month').value = String(Math.max(1, Math.min(12, month)));
  (payload.developer_inputs.checkbox_fields || []).forEach(field => {
    const input = document.querySelector(`input[name="${field}"]`);
    if (input) input.checked = ranked.filter(game => Boolean(game[field])).length >= ranked.length / 2;
  });
  const combo = tagComboCandidates()[0];
  if (combo) {
    combo.combo.split(' + ').forEach(tag => selectedSet('tags').add(tag));
  }
  updateInterface();
}
function renderTagComboRecommendations() {
  const target = document.getElementById('tagComboRecommendations');
  clear(target);
  add(target, node('h3', '선택 장르 기준 성공확률 높은 태그 조합'));
  if (!selectedState.genres.size) {
    add(target, node('p', '메인 장르를 먼저 선택하면, 그 장르에서 성공확률이 높았던 Steam 태그 조합을 추천합니다.', 'muted'));
    return;
  }
  const combos = tagComboCandidates();
  if (!combos.length) {
    add(target, node('p', '현재 선택 장르에서는 표본 2개 이상인 태그 조합이 부족합니다. 더 넓은 장르를 선택해보세요.', 'muted'));
    return;
  }
  add(target, table(['추천 태그 조합','평균 예측','성공률','표본'], combos.map(row => [row.combo, pct(row.probability), pct(row.successRate), row.sample])));
}
function probabilityFor(terms) {
  if (!terms.length) return Number(payload.summary.average_prediction || 0);
  const games = matchingGames(terms);
  if (!games.length) return Number(payload.summary.average_prediction || 0);
  return games.reduce((sum, game) => sum + Number(game.predicted_success_probability || 0), 0) / games.length;
}
function updateChips(baseProbability) {
  document.querySelectorAll('.impact-chip').forEach(button => {
    const type = button.dataset.kind;
    const value = button.dataset.value;
    const active = selectedState[type].has(value);
    const nextTerms = selectedTerms(active ? '' : type, active ? '' : value);
    const impact = Math.abs(probabilityFor(nextTerms) - baseProbability);
    const hasGames = matchingGames(nextTerms).length > 0;
    button.classList.toggle('active', active);
    button.disabled = !active && (!hasGames || impact < 0.005);
    button.setAttribute('data-impact-disabled', button.disabled ? 'true' : 'false');
    button.title = button.disabled ? '현재 선택 조합에서 학습 게임이 없거나 예측 변화가 없습니다.' : `예상 변화 ${pct(impact)}`;
  });
}
function outcomeClass(label) {
  if (label === '성공') return 'label-success';
  if (label === '중박') return 'label-mid';
  return 'label-fail';
}
function renderSelectedGames(games) {
  const target = document.getElementById('selectedGames');
  clear(target);
  if (!games.length) {
    add(target, node('p', '현재 선택 조합과 일치하는 학습 게임이 없습니다. 비활성화된 태그를 해제하거나 더 넓은 장르부터 선택해보세요.', 'muted'));
    return;
  }
  const successReferenceGames = games.filter(game => game.outcome_label === '성공').slice(0, 8);
  const riskReferenceGames = games.filter(game => game.outcome_label !== '성공').slice(-8).reverse();
  const layout = add(target, node('div', '', 'grid cols-2'));
  const successSection = add(layout, node('section', '', 'card'));
  const riskSection = add(layout, node('section', '', 'card'));
  heading(successSection, '성공 참고 게임');
  const successReferenceGamesNode = add(successSection, node('div', '', 'reference-grid'));
  successReferenceGamesNode.id = 'successReferenceGames';
  heading(riskSection, '실패/주의 참고 게임');
  const riskReferenceGamesNode = add(riskSection, node('div', '', 'reference-grid'));
  riskReferenceGamesNode.id = 'riskReferenceGames';
  successReferenceGames.forEach(game => addGameCard(successReferenceGamesNode, game));
  riskReferenceGames.forEach(game => addGameCard(riskReferenceGamesNode, game));
}
function createGameImage(game) {
  if (!game.header_image) return null;
  const image = node('img', '', 'game-image');
  image.src = game.header_image;
  image.alt = `${game.name} Steam 상점 이미지`;
  image.loading = 'lazy';
  return image;
}
function addGameCard(target, game) {
    const card = add(target, node('button', '', 'game-card'));
    card.type = 'button';
    card.onclick = () => openGameDetail(game.appid);
    const image = createGameImage(game);
    if (image) add(card, image);
    add(card, node('b', game.name));
    add(card, node('p', `${game.genres || '장르 없음'} · ${game.steam_tags || '태그 없음'}`, 'muted'));
    add(card, node('span', game.outcome_label, outcomeClass(game.outcome_label)));
    add(card, node('p', `예측 ${pct(game.predicted_success_probability)} · 리뷰 ${num(game.total_reviews)}개 · 긍정률 ${pct(game.positive_rate)}`, 'muted'));
    add(card, node('p', `${game.business_model} · ${game.lifecycle} · 신뢰도 ${game.confidence}`, 'muted'));
    add(card, node('p', semanticProfileText(game), 'muted'));
    add(card, node('p', `플랫폼 ${num(game.platform_count)}개 · 리뷰 성장률 ${game.review_growth_label}`, 'muted'));
    add(card, node('p', game.reference_reason, 'muted'));
}
function openGameDetail(appid) {
  const game = (payload.games || []).find(item => Number(item.appid) === Number(appid));
  if (!game) return;
  const detail = document.getElementById('gameDetail');
  clear(detail);
  const title = add(detail, node('h2', game.name));
  title.id = 'gameDetailTitle';
  const image = createGameImage(game);
  if (image) add(detail, image);
  add(detail, node('span', game.outcome_label, outcomeClass(game.outcome_label)));
  add(detail, node('p', `모델 예측 성공확률 ${pct(game.predicted_success_probability)} / 리뷰 ${num(game.total_reviews)}개 / 긍정률 ${pct(game.positive_rate)}`));
  add(detail, node('p', `장르: ${game.genres || '없음'}`, 'muted'));
  add(detail, node('p', `태그: ${game.steam_tags || '없음'}`, 'muted'));
  add(detail, node('p', `의미 분류: ${game.business_model} / ${game.lifecycle} / ${game.production_context} / 신뢰도 ${game.confidence}`, 'muted'));
  add(detail, node('p', semanticProfileText(game), 'muted'));
  add(detail, node('p', `플랫폼: Windows ${game.platform_windows ? '지원' : '미지원'}, Mac ${game.platform_mac ? '지원' : '미지원'}, Linux ${game.platform_linux ? '지원' : '미지원'}`, 'muted'));
  add(detail, node('p', `리뷰 성장률: ${game.review_growth_label}`, 'muted'));
  add(detail, node('p', game.model_opinion));
  add(detail, node('p', game.reference_reason));
  const link = document.getElementById('steamDetailLink');
  link.href = game.steam_url;
  document.getElementById('gameModal').classList.add('open');
}
function semanticProfileText(game) {
  const profile = game.semantic_profile || {};
  const business = profile.business_model || {};
  const lifecycle = profile.lifecycle || {};
  const production = profile.production_context || {};
  return `항목별 신뢰도: 비즈니스 ${pct(business.confidence || 0)}, 출시상태 ${pct(lifecycle.confidence || 0)}, 제작맥락 ${pct(production.confidence || 0)} · 종합 ${pct(profile.overall_confidence || 0)} (${profile.confidence_band || game.confidence || '낮음'})`;
}
function closeGameDetail() {
  document.getElementById('gameModal').classList.remove('open');
}
function table(headers, rows) {
  const tableNode = node('table');
  const thead = add(tableNode, node('thead'));
  const headRow = add(thead, node('tr'));
  headers.forEach(header => add(headRow, node('th', header)));
  const tbody = add(tableNode, node('tbody'));
  rows.forEach(row => {
    const tr = add(tbody, node('tr'));
    row.forEach(cell => add(tr, node('td', cell)));
  });
  return tableNode;
}
function trendClass(trend) {
  if (trend === '상승') return 'trend-up';
  if (trend === '유지' || trend === '표본 부족') return 'trend-flat';
  return 'trend-down';
}
function trendSymbol(trend) {
  if (trend === '상승') return '↗ 상승';
  if (trend === '유지') return '→ 유지';
  if (trend === '표본 부족') return '→ 표본 부족';
  return '↘ 하락';
}
function renderTrends() {
  const render = (targetId, rows) => {
    const target = document.getElementById(targetId);
    clear(target);
    const tableNode = node('table');
    const thead = add(tableNode, node('thead'));
    const headRow = add(thead, node('tr'));
    ['항목','방향','예측','성공률','표본'].forEach(header => add(headRow, node('th', header)));
    const tbody = add(tableNode, node('tbody'));
    rows.forEach(row => {
      const tr = add(tbody, node('tr'));
      add(tr, node('td', row.name));
      add(tr, node('td', trendSymbol(row.trend), trendClass(row.trend)));
      add(tr, node('td', pct(row.average_prediction)));
      add(tr, node('td', pct(row.success_rate)));
      add(tr, node('td', row.game_count));
    });
    add(target, tableNode);
  };
  render('genreTrends', payload.market_trends || []);
  render('tagTrends', payload.tag_trends || []);
}
function gameTable(rows) {
  const tableNode = node('table');
  const thead = add(tableNode, node('thead'));
  const headRow = add(thead, node('tr'));
  ['게임','장르','예측','리뷰','긍정률'].forEach(header => add(headRow, node('th', header)));
  const tbody = add(tableNode, node('tbody'));
  rows.forEach(game => {
    const tr = add(tbody, node('tr'));
    const linkCell = add(tr, node('td'));
    const link = add(linkCell, node('a', game.name));
    link.href = game.steam_url;
    link.target = '_blank';
    link.rel = 'noreferrer';
    [game.genres, pct(game.predicted_success_probability), num(game.total_reviews), pct(game.positive_rate)].forEach(cell => add(tr, node('td', cell)));
  });
  return tableNode;
}
function renderGames() {
  const success = document.getElementById('successGames');
  const risk = document.getElementById('riskGames');
  clear(success); clear(risk);
  const successGrid = add(success, node('div', '', 'reference-grid'));
  const riskGrid = add(risk, node('div', '', 'reference-grid'));
  (payload.similar_games.success_examples || []).forEach(game => addGameCard(successGrid, game));
  (payload.similar_games.risk_examples || []).forEach(game => addGameCard(riskGrid, game));
  renderNoEvidenceReferences(success, payload.similar_games.success_without_review_evidence || []);
  renderNoEvidenceReferences(risk, payload.similar_games.risk_without_review_evidence || []);
}
function renderNoEvidenceReferences(target, games) {
  if (!games.length) return;
  heading(target, '리뷰 근거 없는 참고');
  add(target, node('p', '리뷰 본문 표본이 5개 미만이라 모델 지표와 Steam 메타데이터만 참고합니다.', 'muted'));
  const grid = add(target, node('div', '', 'reference-grid'));
  games.forEach(game => addGameCard(grid, game));
}
function renderCautions() {
  const rec = payload.recommendations;
  const target = document.getElementById('cautions');
  clear(target);
  add(target, node('p', rec.priority_basis));
  heading(target, '주의 키워드');
  rec.development_cautions.forEach(item => add(target, node('span', item, 'pill risk')));
  heading(target, '강점 키워드');
  rec.positioning_strengths.forEach(item => add(target, node('span', item, 'pill')));
}
function renderExternal() {
  const target = document.getElementById('external');
  clear(target);
  Object.entries(payload.external_data).forEach(([key, value]) => {
    const card = add(target, node('div', '', `card ${value.enabled ? 'enabled' : 'disabled'}`));
    add(card, node('b', key));
    add(card, node('p', value.reason));
  });
}
function renderImportance() {
  const target = document.getElementById('importance');
  clear(target);
  const rows = payload.feature_importance || [];
  if (!rows.length) {
    add(target, node('p', 'feature importance 데이터 부족', 'muted'));
    return;
  }
  rows.forEach(row => {
    const wrapper = add(target, node('div'));
    const featureName = add(wrapper, node('b', row.feature));
    featureName.title = featureHelpText(row);
    add(wrapper, node('span', ` 중요도 ${pct(row.importance)}`, 'muted'));
    const bg = add(wrapper, node('div', '', 'bar-bg'));
    const bar = add(bg, node('div', '', 'bar'));
    bar.style.width = `${Math.min(100, Number(row.importance || 0) * 100).toFixed(1)}%`;
  });
}
function featureHelpText(row) {
  return row.importance_description || '모델 학습 과정에서 성공/실패 구분에 사용된 입력 변수입니다.';
}
function renderComparison() {
  const target = document.getElementById('comparison');
  clear(target);
  const games = payload.games || [];
  const platformAverage = games.length ? games.reduce((sum, game) => sum + Number(game.platform_count || 0), 0) / games.length : 0;
  const growthAvailable = games.filter(game => Number(game.review_count_30d || 0) || Number(game.review_count_90d || 0)).length;
  add(target, node('p', `평균 플랫폼 지원 수: ${platformAverage.toFixed(1)}개`));
  add(target, node('p', `리뷰 성장률 데이터 보유 게임: ${num(growthAvailable)}개 / ${num(games.length)}개`));
  if (!growthAvailable) add(target, node('p', '현재 학습 데이터에는 review_count_30d/review_count_90d가 없어 상세 카드에서 데이터 부족으로 표시합니다.', 'muted'));
}
function estimate() {
  const terms = selectedTerms();
  const matchedGames = matchingGames(terms);
  const base = probabilityFor(terms);
  const price = Number(document.getElementById('price')?.value || 0);
  const languages = Number(document.getElementById('languages')?.value || 0);
  const releaseMonth = Number(document.getElementById('month')?.value || 0);
  const detailedChecks = payload.developer_inputs.checkbox_fields || [];
  const checkedDetails = detailedChecks.filter(field => document.querySelector(`input[name="${field}"]`)?.checked).length;
  const seasonalAdjustment = [2,3,9,10,11].includes(releaseMonth) ? 0.02 : 0;
  const adjustment = Math.min(0.14, languages * 0.005 + checkedDetails * 0.015 + seasonalAdjustment) - (price > 40 ? 0.05 : 0);
  const probability = Math.max(0, Math.min(1, base + adjustment));
  const target = document.getElementById('estimate');
  clear(target);
  add(target, node('h3', '선택 기획 잠재력'));
  add(target, node('span', pct(probability), 'metric'));
  add(target, node('p', `기획 입력 반영: 선택한 장르/태그 ${terms.length}개, 매칭 게임 ${matchedGames.length}개, 가격, 언어 수, 출시월, 플랫폼/멀티플레이/컨트롤러/도전과제 선택값을 학습 데이터의 평균 예측값에 반영했습니다.`, 'muted'));
  renderTagComboRecommendations();
  renderSelectedGames(matchedGames);
  updateChips(base);
}
function updateInterface() {
  estimate();
}
function activateTab(name) {
  document.querySelectorAll('.tab-button').forEach(button => button.classList.toggle('active', button.dataset.tab === name));
  document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.toggle('active', panel.id === `tab-${name}`));
}
document.querySelectorAll('.tab-button').forEach(button => {
  button.onclick = () => activateTab(button.dataset.tab);
});
document.getElementById('gameModal').addEventListener('click', event => {
  if (event.target.id === 'gameModal') closeGameDetail();
});
renderSummary(); renderGuidance(); renderSemanticModel(); renderInputs(); renderTrends(); renderGames(); renderCautions(); renderExternal(); renderImportance(); renderComparison(); updateInterface();
</script>
</body>
</html>
"""
