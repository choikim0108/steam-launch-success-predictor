# 다음 세션 전달용 미구현·개선 이슈 가이드

이 문서는 현재 Steam 시장 인사이트 리포트의 남은 이슈와 다음 실행 순서를 빠르게 이어받기 위한 작업 가이드다. 2026-06-06 기준 최신 구현 커밋은 `e446a74 Add 90d market insight report`이며, 90일 기준 리포트는 `reports/90d/market_insight_site.html`과 `reports/90d/interactive_report.html`이다.

## 현재 구현 완료 상태

- 2025~2026 Steam release-window appid 수집을 완료했다.
- appdetails/review summary 수집을 checkpoint resume으로 전체 release-window까지 확장했다.
- review histogram 수집과 7/30/90일 전처리를 완료했다.
- 90일 전용 CLI `steam_success.pipeline_90d`를 추가했고, 기존 누적 리뷰 기준 산출물과 별도 경로에 저장한다.
- 내 게임 진단 UI는 `성공 가능성 / 비교군 / 위험 / 액션 제안` 4단 구성으로 표시한다.
- 장르/태그 조합 추천은 충분 표본 기준 이상만 강하게 추천하고, 부족한 조합은 `탐색 후보 / 표본 부족`으로 분리한다.
- coverage/confidence, small-sample smoothing, 참고 게임 리뷰 근거 분리, 하드코딩 문서화는 구현돼 있다.

## 현재 90일 산출물 수치

- `data/interim/search_release_window_appids.csv`: 29,298개 고유 appid
- `data/raw/steam_appdetails.csv`, `data/raw/steam_review_summaries.csv`: 29,345개 성공 row
- `data/interim/game_candidates_2025_2026.csv`: 29,018개 후보, 22,473개 `label_eligible_90d`
- `data/raw/steam_review_histogram_status.csv`: 22,473개 90일 라벨 가능 appid 수집 성공, 그중 2,128개는 rollup row 0개
- `data/raw/steam_review_histogram.csv`: 20,345개 row 보유 appid, 266,674개 histogram row
- `data/interim/game_review_windows_2025_2026.csv`: 29,018개 후보, 22,473개 라벨 가능 row, 636개 `success_90d`
- `reports/90d/market_insight_site.html`: 90일 라벨 가능 22,473개 기준 정적 시장 인사이트 리포트

원천 검색 appid 수보다 appdetails row가 조금 많은 것은 이전 checkpoint/raw cache에 남아 있던 추가 appid row까지 합쳐졌기 때문이다. 리포트 coverage는 `search_release_window_appids.csv`의 29,298개 모집단을 기준으로 계산한다.

## 90일 전용 실행 명령

```bash
PYTHONPATH=src python3 -m steam_success.collect.search_release_window --start-year 2025 --end-year 2026 --stop-before-year 2025 --sleep-seconds 1.5
PYTHONPATH=src python3 -m steam_success.collect.appdetails_for_appids --input-csv data/interim/search_release_window_appids.csv --sleep-seconds 1.0 --max-retries 5 --flush-every 100
PYTHONPATH=src python3 -m steam_success.preprocess.candidate_filter --start-year 2025 --end-year 2026
PYTHONPATH=src python3 -m steam_success.collect.review_histogram --input-csv data/interim/game_candidates_2025_2026.csv --only-label-eligible-90d --flush-every 500 --sleep-seconds 0.5
PYTHONPATH=src python3 -m steam_success.preprocess.review_windows
PYTHONPATH=src python3 -m steam_success.pipeline_90d
```

`appdetails_for_appids`와 `review_histogram`은 기존 CSV와 raw JSON을 읽고 완료된 appid를 건너뛰므로 timeout 이후 같은 명령을 재실행하면 이어서 수집한다.

## 아직 남은 한계

- `reports/90d/market_insight_site.html`은 22,473개 게임 payload를 self-contained HTML 안에 넣기 때문에 브라우저 상호작용이 느릴 수 있다. 최적화하려면 payload 축소, term index, 페이지네이션, 사전 집계 추천 데이터가 필요하다.
- 실제 브라우저 클릭 QA는 아직 없다. 현재 검증은 HTML 파싱과 테스트 중심이다.
- 참고 게임별 대표 긍정/부정 리뷰 snippet을 모달에 보여주는 UI는 아직 없다.
- SteamDB 연도별 출시 수 같은 외부 coverage 기준 자동 연결은 아직 제한적이다.

## 검증 명령

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test*.py'
PYTHONPATH=src python3 -m compileall src tests
python3 - <<'PY'
from pathlib import Path
import json, re
html = Path('reports/90d/market_insight_site.html').read_text(encoding='utf-8')
payload = json.loads(re.search(r'<script id="market-data" type="application/json">(.*?)</script>', html, re.S).group(1))
print(payload['summary'])
PY
```
