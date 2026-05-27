# 에이전트 작업 규칙

이 프로젝트에서 작업하는 에이전트는 작업 지시를 수행하기 전에 이 문서를 먼저 읽는다.

## 작업 전 확인 순서
1. `README.md`에서 프로젝트 목적과 성공 기준을 확인한다.
2. `docs/WORKSPACE_DOCUMENTS.md`에서 문서와 산출물 경로를 확인한다.
3. `docs/MANUAL.md`에서 실행/검증 방법을 확인한다.
4. 코드 변경 전 `src/steam_success/`의 기존 모듈 분리를 유지할 수 있는지 확인한다.

## 변경 원칙
- 크롤링/전처리/피처/모델/시각화/리포트 생성을 각각의 기존 모듈에 맞춰 수정한다.
- 생성 산출물은 `reports/`, 설명 문서는 `docs/`, 원천 데이터는 `data/raw/`에 둔다.
- 루트의 과제 PDF, WBS, CSV, XLSX 원본 자료는 참조 경로 보존을 위해 이동하지 않는다.
- `reports/interactive_report.html`에는 최종 질문인 "그래서 성공할 것으로 예측되는 게임은 뭔가?"에 대한 답과 Steam 링크가 포함되어야 한다.

## 검증 기준
- 코드 변경 후 `python3 -m compileall src`를 실행한다.
- 가능하면 `PYTHONPATH=src python3 run_pipeline.py`로 전체 산출물을 재생성한다.
- HTML 변경은 `reports/interactive_report.html`을 실제로 열거나 파싱해서 결론, Steam 링크, 이미지 경로가 존재하는지 확인한다.
