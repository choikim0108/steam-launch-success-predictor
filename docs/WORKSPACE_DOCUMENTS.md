# 문서 및 경로 정리

## 먼저 읽을 문서
- `AGENTS.md`: 에이전트 작업 전 필수 규칙
- `README.md`: 프로젝트 목적, 데이터 계획, 성공 기준
- `docs/TEAM_PROJECT_PLAN.md`: 팀 일정, 역할, 단계별 실행 계획
- `docs/DATA_COLLECTION_RUNBOOK.md`: 데이터 수집 실행 순서
- `docs/DATA_COLLECTION_ATTEMPTS.md`: 1차~3차 수집 시도 결과와 병목 보고
- `docs/DATA_COLLECTION_STRUCTURE_KO.md`: 현재 수집 중인 데이터 구조와 각 컬럼 한글 설명
- `docs/DATA_COLLECTION_CODE_FLOW_KO.md`: 데이터 수집 명령과 내부 코드 흐름 설명
- `docs/ARCHITECTURE.md`: 90일 성공 예측 파이프라인 구조
- `docs/MANUAL.md`: 명령어와 산출물 위치

## 주요 경로
- `src/steam_success/`: 크롤링, 전처리, 피처, 모델링, 시각화, 리포트 생성 코드
- `data/raw/`: Steam 검색 HTML, Store API, Reviews API 원천 수집 결과
- `data/interim/`: 병합된 중간 데이터
- `data/processed/`: 모델 학습용 데이터
- `reports/`: CSV/JSON 평가 결과, 결론 Markdown, HTML 리포트
- `reports/figures/`: HTML에 포함되는 최신 PNG 시각화
- `reports/experience_scenario.html`: 사용자 경험 중심 시각화 문서
- `models/`: 학습된 모델 파일
- `docs/`: 핵심 실행 문서
- `docs/reference/`: 참고용 상세 문서, 과거 가이드, 질문 목록, PDF 요약
- `legacy/current_snapshot/`: 현재 누적 리뷰 기준으로 생성된 초기 모델/리포트 보존본

## 작업공간 루트 참고 자료
- `dmP/1조 게임 (1).pdf`: 팀 프로젝트 참고 PDF
- `dmP/20260518_[데이터마이닝] 2026기말프로젝트.pdf`: 과제 설명 PDF
- `dmP/WBS_초안_주제1_주제4.md` 및 CSV/XLSX 파일: 초기 일정/역할/브레인스토밍 자료

루트의 원본 과제 자료는 제출/참고 경로가 바뀌지 않도록 이동하지 않는다. 프로젝트 내부 산출물 문서는 `docs/`와 `reports/`로 구분해 관리한다.
