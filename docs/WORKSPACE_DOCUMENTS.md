# 문서 및 경로 정리

## 먼저 읽을 문서
- `AGENTS.md`: 에이전트 작업 전 필수 규칙
- `README.md`: 프로젝트 목적, 데이터 계획, 성공 기준
- `docs/MANUAL.md`: 실행 방법과 산출물 위치

## 주요 경로
- `src/steam_success/`: 크롤링, 전처리, 피처, 모델링, 시각화, 리포트 생성 코드
- `data/raw/`: Steam 검색 HTML, Store API, Reviews API 원천 수집 결과
- `data/interim/`: 병합된 중간 데이터
- `data/processed/`: 모델 학습용 데이터
- `reports/`: CSV/JSON 평가 결과, 결론 Markdown, HTML 리포트
- `reports/figures/`: HTML에 포함되는 최신 PNG 시각화
- `models/`: 학습된 모델 파일
- `docs/`: 프로젝트 설명, 아키텍처, 실행 매뉴얼, 가정/질문, PDF 요약

## 작업공간 루트 참고 자료
- `dmP/1조 게임 (1).pdf`: 팀 프로젝트 참고 PDF
- `dmP/20260518_[데이터마이닝] 2026기말프로젝트.pdf`: 과제 설명 PDF
- `dmP/WBS_초안_주제1_주제4.md` 및 CSV/XLSX 파일: 초기 일정/역할/브레인스토밍 자료

루트의 원본 과제 자료는 제출/참고 경로가 바뀌지 않도록 이동하지 않는다. 프로젝트 내부 산출물 문서는 `docs/`와 `reports/`로 구분해 관리한다.
