# 에이전트 작업 규칙

이 프로젝트에서 작업하는 에이전트는 작업 지시를 수행하기 전에 이 문서를 먼저 읽는다.

## 작업 전 확인 순서
1. `README.md`에서 프로젝트 목적과 성공 기준을 확인한다.
2. `docs/DATA_COLLECTION_RUNBOOK.md`에서 현재 수집 기준과 실행 순서를 확인한다.
3. `docs/DATA_COLLECTION_ATTEMPTS.md`에서 이미 확인한 수집 리스크와 측정값을 확인한다.
4. `docs/ARCHITECTURE.md`에서 90일 성공 예측 파이프라인을 확인한다.
5. `docs/MANUAL.md`에서 실행/검증 명령을 확인한다.
6. 코드 변경 전 `src/steam_success/`의 기존 모듈 분리를 유지할 수 있는지 확인한다.

## 현재 기준 방향
- 메인 분석 범위는 2025~2026 Steam 출시 게임이다.
- 메인 appid 수집 루트는 Steam 상점 검색 `Released_DESC` 최신순 크롤링이다.
- 공식 `IStoreService/GetAppList`, SteamSpy, SteamDB는 메인 수집이 아니라 누락/편향 검증용 보조 축이다.
- `success_90d` 모델 학습 라벨은 출시 후 90일이 지난 게임에만 만든다. 현재 기준일은 2026-06-01이고, 학습 라벨 가능 기준은 `release_date <= 2026-03-03`이다.
- 2026-03-04 이후 출시 게임은 최신 트렌드와 예측 대상에는 포함하지만 모델 학습 정답에는 포함하지 않는다.

## 변경 원칙
- 크롤링/전처리/피처/모델/시각화/리포트 생성을 각각의 기존 모듈에 맞춰 수정한다.
- 생성 산출물은 `reports/`, 설명 문서는 `docs/`, 원천 데이터는 `data/raw/`에 둔다.
- Steam 상점 검색 크롤링은 429 방지를 위해 기본 sleep, retry/backoff, 페이지별 raw 저장, checkpoint CSV 갱신을 유지한다.
- 루트의 과제 PDF, WBS, CSV, XLSX 원본 자료는 참조 경로 보존을 위해 이동하지 않는다.
- `reports/90d/interactive_report.html`에는 최종 질문인 "그래서 성공할 것으로 예측되는 게임은 뭔가?"에 대한 답과 Steam 링크가 포함되어야 한다.

## 검증 기준
- 코드 변경 후 `PYTHONPATH=src python -m compileall src tests`를 실행한다.
- 테스트 변경 후 `PYTHONPATH=src python -m unittest discover -s tests`를 실행한다.
- 수집 CLI 변경 후 `steam_success.collect.search_release_window --max-pages 2` smoke test를 temp root에서 실행한다.
- 기존 `run_pipeline.py`는 현재 누적 리뷰 기준 레거시 흐름이므로 90일 수집 검증으로 사용하지 않는다.
- HTML 변경은 `reports/90d/interactive_report.html` 또는 `reports/90d/market_insight_site.html`을 실제로 열거나 파싱해서 결론, Steam 링크, 이미지 경로가 존재하는지 확인한다.
