# 관측 결과와 기획 예측 분리 리포트 재설계 계획

## 목적

현재 수집된 게임들은 이미 출시 후 90일 성과가 관측된 표본이므로, 게임 카드에서 `예측`이라는 표현으로 개별 게임을 평가하지 않는다. 카드의 주 역할은 `관측 결과`와 `근거 사례` 표시로 바꾸고, 예측은 게임 개발자가 입력한 장르/태그/기획 조건에 대해 성공 가능성, 표본 근거, 조합 추천을 계산하는 용도로만 사용한다.

최종 HTML은 다음 두 질문에 집중한다.

1. 개발자가 선택한 장르/태그가 성장세에 있는지, 어떤 조합을 했을 때 어떤 근거로 어느 정도 성공률 또는 잠재력이 나오는가?
2. 현재 성장세에 있는 장르/태그 조합은 무엇인가?

## 현재 코드에서 바꿔야 할 지점

`src/steam_success/market_report.py`는 `reports/90d/market_insight_site.html`을 생성한다. 현재 카드와 테이블은 `예측`, `평균 예측`, `모델 예측 성공확률`을 관측 완료 게임 카드에도 표시한다. 이 표현은 개발자 입력 진단 영역으로 옮기고, 개별 게임 카드에는 `관측 결과`, `90일 리뷰`, `90일 긍정률`, `성공/중박/실패 라벨`, `리뷰 성장률`, `Steam 링크`, `근거 사례`만 남긴다.

`src/steam_success/market_insight.py`는 이미 장르/태그별 `success_rate`, `average_prediction`, `game_count`, `trend`를 만들고, `developer_inputs`, `developer_guidance`, `market_trends`, `tag_trends`, `games` payload를 생성한다. 구현 계획에서는 이 구조를 유지하되 `average_prediction`의 표시 위치와 이름을 바꾼다. 관측 표본에서는 `model_probability`보다 `observed_success_rate`와 `sample_size`를 앞세우고, 개발자 입력 결과에서만 `estimated_success_probability` 또는 `기획 잠재력`으로 표시한다.

`src/steam_success/web_report.py`의 `그래서 성공할 것으로 예측되는 게임은 뭔가?` 섹션은 새 방향과 충돌한다. 최종 제출에 계속 포함해야 하는지 AGENTS.md에는 남아 있지만, 사용자 의도 기준으로는 개별 출시 게임 예측이 아니라 `성공 가능성이 높은 기획 조합` 또는 `성장 조합` 답변으로 교체하는 것이 맞다.

## 모델 사용 계획

새 `조합 단위 집계 모델`을 추가한다. 현재 90일 성공 분류 모델은 feature importance와 보조 검증 근거로 유지하지만, HTML의 중심 결과는 개별 게임 확률이 아니라 장르/태그 조합 단위의 opportunity score가 담당한다.

- 관측 게임 카드: 모델 확률 숨김, 관측 결과 중심 표시
- 개발자 입력 진단: 선택 장르/태그와 상세 조건을 조합 집계 모델에 매칭해 성공 잠재력 산출
- 성장 조합: 관측 표본의 성공률, 표본 수, 30일 대비 90일 리뷰 증가량, 최근 출시연도/출시월 분포, 객관적으로 접근 가능한 보조 요소를 함께 사용해 ranking

모델 2는 복잡한 ML이 아니라 조합 단위 설명형 집계 모델로 둔다. 입력은 장르/태그 조합, 표본 수, 관측 성공률, smoothed success rate, 30→90일 리뷰 성장률, 최근 출시 비중, 가격대 안정성, 언어 지원 수준, 플랫폼/기능 지원 밀도, 외부 관심도 보유 여부, 리뷰 근거 보유 여부다. 출력은 `opportunity_score`, `growth_label`, `evidence_lines`, `recommended_combinations`다.

## HTML 재설계 범위

`reports/90d/market_insight_site.html`은 4개 탭 이하로 줄인다.

1. `성장 조합`: 현재 성장세 장르/태그 조합 ranking, 성공률, 표본 수, 리뷰 성장 근거 표시
2. `내 기획 진단`: 개발자가 선택한 장르/태그/상세 조건의 잠재력, 근거 표본, 성공률, 추천 태그 조합 표시
3. `근거 사례`: 선택 조건과 유사한 관측 성공/중박/실패 게임 카드 표시. 카드 제목은 예측이 아니라 관측 결과 기준
4. `판단 기준`: 모델 feature importance, success_90d 기준, 표본 부족/coverage/주의사항 표시

삭제 또는 축소 대상은 `평균 예측 확률` 중심 요약, 개별 게임 `예측` 문구, “성공할 것으로 예측되는 게임” 단일 답변, 외부 데이터 상태가 비어 있는 독립 강조 섹션이다. 외부 데이터는 있으면 판단 기준 하위에 두고, 없으면 작은 비활성 카드로만 표시한다.

## 데이터와 지표 정의

성장세는 기본적으로 조합 단위의 `관측 성공률 + smoothed success rate + 리뷰 성장률 + 최근성`으로 정의한다. 최소 표본 수 미만 조합은 `탐색 후보`로 분리하고, ranking 상단에는 올리지 않는다.

권장 필드:

- `combination`: 장르 1개 이상 + 태그 0~2개 조합
- `game_count`: 조합에 매칭된 관측 게임 수
- `success_count`, `success_rate`, `smoothed_success_rate`
- `avg_reviews_30d`, `avg_reviews_90d`, `review_growth_ratio`
- `recent_share`: 2026 또는 최근 출시월 비중
- `opportunity_score`: 성공률, 성장률, 표본 안정성을 결합한 점수
- `evidence`: “표본 n개, 성공률 x%, 30→90일 리뷰 y배, 성공 사례 A/B” 형식의 설명

## 구현 순서

1. 테스트로 현재 금지 표현을 먼저 고정한다. 관측 게임 카드 HTML에 `예측` 문구가 나오면 실패하고, 개발자 입력 진단에는 잠재력/성공률/근거가 나와야 한다.
2. `market_insight.py`에 조합 단위 opportunity payload를 추가한다. 기존 `market_trends`, `tag_trends`는 유지하되 표시명과 근거 필드를 보강한다.
3. `market_report.py` HTML 탭과 JS 렌더링을 두 질문 중심으로 축소한다. 카드 문구는 `관측 결과`, `기획 잠재력`, `근거 표본`으로 통일한다.
4. `web_report.py`와 `RUN_SUMMARY.md`의 단일 게임 예측 문구를 조합/기획 진단 문구로 바꾼다. 단, 제출 요구 때문에 interactive report에 기존 질문 문구를 남겨야 한다면 답변 내용만 “게임”이 아닌 “기획 조합”으로 바꾼다.
5. 90일 파이프라인을 재실행해 `reports/90d/market_insight_site.html`과 `reports/90d/interactive_report.html`을 재생성한다.
6. 브라우저 또는 HTML 파싱으로 금지 문구, Steam 링크, 조합 ranking, 내 기획 진단 동작을 검증한다.

## 검증 시나리오 계약

### 시나리오 1: Happy path

- 조건: 사용자가 충분한 표본이 있는 장르와 태그를 선택한다.
- 통과 조건: `내 기획 진단`이 잠재력 수치, 관측 성공률, 표본 수, 추천 태그 조합, 유사 성공/실패 사례를 표시하고 관측 게임 카드에는 `예측` 문구가 없다.
- 테스트 후보: `tests/test_market_insight_site.py::test_developer_planner_uses_prediction_only_for_selected_concept`
- 실제 표면: `reports/90d/market_insight_site.html`을 열거나 파싱해 `market-data` payload와 렌더링 문구 확인

### 시나리오 2: Edge / 표본 부족 조합

- 조건: 사용자가 매칭 게임이 없거나 최소 표본 수 미만인 조합을 선택한다.
- 통과 조건: 강한 추천을 하지 않고 `탐색 후보 / 표본 부족`을 표시하며, 성공률을 확정 결론처럼 말하지 않는다.
- 테스트 후보: `tests/test_market_insight_site.py::test_sparse_combination_is_exploratory_not_recommended`
- 실제 표면: 정적 HTML에서 희소 조합 선택 후 표본 부족 문구 확인

### 시나리오 3: 성장 조합 ranking

- 조건: 여러 장르/태그 조합의 성공률은 비슷하지만 표본 수와 30→90일 리뷰 성장률이 다르다.
- 통과 조건: 충분 표본과 성장 근거가 있는 조합이 상위에 오르고, tiny perfect 조합은 탐색 후보로 분리된다.
- 테스트 후보: `tests/test_market_insight_site.py::test_growth_combinations_rank_by_sample_smoothed_success_and_review_growth`
- 실제 표면: `성장 조합` 탭에 조합명, 성공률, 성장 근거, 표본 수 표시 확인

### 시나리오 4: Adjacent regression

- 조건: 90일 파이프라인을 실행해 최종 HTML과 요약 문서를 재생성한다.
- 통과 조건: `reports/90d/market_insight_site.html`, `reports/90d/interactive_report.html`, `reports/90d/RUN_SUMMARY.md`가 생성되고, 개별 관측 게임을 `성공할 것으로 예측`한다고 표현하지 않는다.
- 테스트 후보: `tests/test_pipeline_90d.py::test_pipeline_writes_opportunity_focused_reports`
- 실제 표면: `PYTHONPATH=src python3 -m steam_success.pipeline_90d` 실행 및 HTML 파싱

## 사용자 응답 반영 확정 사항

`interactive_report.html`의 기존 질문은 “그래서 성공할 것으로 예측되는 게임은 뭔가?”에서 “성공 가능성이 높은 기획/장르·태그 조합은 뭔가?”로 교체한다. 개별 출시 게임은 더 이상 예측 대상으로 표현하지 않고, 이미 결과가 관측된 참고 사례로만 표시한다.

성장세 ranking은 단순 성공률이나 리뷰 성장률 하나로 정하지 않고 업그레이드된 `opportunity_score`를 사용한다. 기본 구성은 성공률, smoothed success rate, 표본 수 안정성, 30→90일 리뷰 성장률, 최근 출시 비중이며, 현재 데이터에서 객관적으로 접근 가능하고 의미 있는 요소가 있으면 추가한다. 추가 후보는 가격대 안정성, 언어 지원 수준, 플랫폼/기능 지원 밀도, 외부 관심도 보유 여부, 리뷰 근거 보유 여부다. 단, 현재 시점 결과나 외부 관심도는 예측 입력이 아니라 조합 ranking의 설명 보조 근거로만 사용한다.

개발자 입력 예측/추천 엔진은 새 `조합 단위 집계 모델`을 추가하는 방향으로 구현한다. 이 모델은 개별 게임 성공 확률을 보여주는 모델이 아니라 장르/태그 조합별 표본, 관측 성공률, 성장률, 최근성, 안정성을 집계해 `opportunity_score`, `growth_label`, `evidence_lines`, `recommended_combinations`를 만드는 설명형 모델이다. 기존 90일 분류 모델은 feature importance와 보조 검증 근거로 유지하되, HTML의 중심 결과는 조합 집계 모델이 담당한다.

## 업데이트된 구현 결정

1. `market_insight.py`에 `combination_opportunities` payload를 추가한다.
2. `market_report.py`의 메인 탭은 `성장 조합`과 `내 기획 진단`을 최우선으로 재배치한다.
3. 관측 게임 카드에서는 `예측`, `평균 예측`, `모델 예측 성공확률`을 제거하고 `관측 결과`, `90일 리뷰`, `긍정률`, `근거 사례`만 표시한다.
4. `web_report.py`의 단일 top predicted game payload는 combination opportunity payload로 교체한다.
5. 테스트 이름과 검증 시나리오는 조합 단위 모델 기준으로 고정한다.
