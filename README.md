# Steam 90일 출시 성과 분석 및 기획 인사이트

데이터마이닝 기말 프로젝트 1조 저장소입니다. 이 프로젝트는 2025~2026년 Steam 출시 게임 데이터를 수집·정제하고, 출시 후 90일 리뷰 성과를 기준으로 장르/태그/상점 기능 조합의 시장성을 분석합니다.

최종 결과물은 개별 게임을 “앞으로 성공할 게임”으로 예측하는 리포트가 아니라, 이미 관측된 Steam 출시 성과를 바탕으로 개발자가 선택한 기획 조건의 참고 사례와 성장 조합을 설명하는 리포트입니다.

## 프로젝트 개요

- 프로젝트: 1조 Steam 90일 출시 성과 분석 및 기획 인사이트
- 분석 범위: 2025~2026년 Steam 출시 게임
- 핵심 질문:
  - 출시 후 90일 리뷰 성과 기준으로 어떤 장르/태그/기능 조합이 좋은 성과를 보였는가?
  - 개발자가 선택한 장르와 태그 조건에서 참고할 관측 성공 사례와 관측 실패/주의 사례는 무엇인가?
  - 가격, 지원 언어 수, 플랫폼, 컨트롤러/도전과제 등 출시 전 설정 가능한 요소는 기획 판단에 어떤 근거를 주는가?
- 최종 산출물:
  - `reports/90d/market_insight_site.html`: 발표·시연용 시장 인사이트 HTML
  - `reports/90d/interactive_report.html`: 기준별 관측 성공률을 확인하는 인터랙티브 HTML
  - `reports/90d/RUN_SUMMARY.md`: 90일 파이프라인 실행 요약
  - `reports/90d/CONCLUSIONS.md`: 주요 결론 요약
  - `models/90d/steam_success_model.joblib`: 90일 성공 분류 모델 artifact
  - `presentation/final_90d_black/steam_success_90d_black_deck.pptx`: 최종 발표 자료
  - `presentation/구현영상_대본.md`: 구현 영상 설명 대본
  - `presentation/system_pipeline_diagram.png`: 수집·전처리·모델링·리포트 파이프라인 구조도
  - `presentation/video_section4_model_comparison.png`: 구현 영상 모델 성능 비교 보조 이미지
  - `presentation/video_section5_usage_limits.png`: 구현 영상 활용 범위와 한계 보조 이미지

## 데이터와 기준

### 메인 데이터

1. Steam 상점 검색 최신순 직접 크롤링 데이터
   - `Released_DESC`, `category1=998` 기준으로 2025~2026 출시 구간 appid 수집
   - appid, 게임명, 검색 출시일, 검색 가격, 검색 페이지 위치 저장
2. Steam appdetails API 데이터
   - 출시일, 가격, 장르, 카테고리, 플랫폼, 지원 언어, 상점 기능 정보 수집
3. Steam 리뷰 데이터
   - 출시 후 30일/90일 리뷰 수와 긍정률을 사용해 관측 성과 산출

### 90일 성공 기준

Steam은 실제 판매량을 공개하지 않으므로 출시 후 90일 리뷰 수와 긍정률을 흥행 대체 지표로 사용합니다.

```text
success_90d = 출시 후 90일 리뷰 수 >= 500 AND 출시 후 90일 긍정률 >= 80%
```

현재 기준일은 `2026-06-01`입니다. 따라서 `success_90d` 학습 라벨은 `release_date <= 2026-03-03` 게임에만 생성됩니다.

## 분석 및 리포트 구성

### 90일 성공 분류 모델

- 가격, 지원 언어 수, Steam 카테고리/기능, 플랫폼, 장르 수 등 출시 전 또는 초기 상점 정보 중심 feature를 사용합니다.
- 모델 결과는 개별 관측 게임을 예측 대상으로 표시하기보다 feature importance와 판단 기준 설명에 사용합니다.

### 조합 단위 기획 인사이트

- 장르와 Steam 태그/기능 조합별로 관측 성공률, 표본 수, 30→90일 리뷰 성장률, 최근 출시 비중을 집계합니다.
- `opportunity_score`를 통해 성장 조합 ranking을 만들고, 표본 부족 조합은 탐색 후보로 분리합니다.

### HTML 리포트 탭

`reports/90d/market_insight_site.html`은 다음 탭으로 구성됩니다.

1. `성장 조합`: 현재 표본에서 좋은 성과를 보인 장르/태그 조합 ranking
2. `내 기획 진단`: 사용자가 선택한 장르/태그/상세 조건의 기획 잠재력과 선택 조건 기반 참고 게임
3. `근거 사례`: 전체 데이터 기준 관측 성공 사례와 관측 실패/주의 사례
4. `판단 기준`: 모델 feature importance, 성공/중박/실패 기준, 모델·파이프라인 구조

## 발표 및 구현 영상 자료

- `presentation/final_90d_black/`: 최종 발표 PPTX와 발표 대본, 평가기준 반영 체크리스트
- `presentation/system_pipeline_diagram.png`: 구현 영상 2번 구간에서 사용하는 전체 시스템 파이프라인 설명 이미지
- `reports/90d/market_insight_site.html`: 구현 영상 3번 구간에서 실제 개발자 활용 시나리오를 보여주는 HTML 리포트
- `presentation/video_section4_model_comparison.png`: 구현 영상 4번 구간에서 Logistic Regression과 Random Forest 성능을 비교하는 이미지
- `presentation/video_section5_usage_limits.png`: 구현 영상 5번 구간에서 활용 가능성과 한계를 정리하는 이미지
- `presentation/구현영상_대본.md`: 위 자료를 순서대로 설명하기 위한 구현 영상 대본

## 현재 프로젝트 구조

```text
.
├── data/
│   ├── raw/                 # 원천 수집 데이터, raw API/cache 파일
│   ├── interim/             # 중간 정제 데이터와 2025~2026 후보/리뷰 윈도우
│   └── processed/           # 모델링 데이터셋
├── docs/                    # 수집 runbook, 아키텍처, 리포트 설계 문서
├── legacy/                  # 이전 현재 누적 리뷰 기준 실험 보존본
├── models/
│   ├── 90d/                 # 90일 모델 artifact
│   └── steam_success_90d_model.joblib
├── presentation/            # 발표 자료
├── reports/
│   └── 90d/
│       ├── market_insight_site.html
│       ├── interactive_report.html
│       ├── RUN_SUMMARY.md
│       ├── CONCLUSIONS.md
│       ├── criteria_*.csv
│       ├── feature_importance.csv
│       ├── model_metrics.*
│       ├── predictions.csv
│       └── figures/
├── scripts/                 # 보조 실행 스크립트
├── src/
│   └── steam_success/
│       ├── collect/         # Steam 검색/appdetails/review/external 보조 수집
│       ├── features/        # 모델 feature 정의
│       ├── models/          # 학습/평가 코드
│       ├── preprocess/      # 후보 필터링, 리뷰 윈도우 전처리
│       ├── visualize/       # 차트 생성
│       ├── pipeline_90d.py  # 90일 기준 메인 파이프라인
│       ├── market_insight.py
│       ├── market_report.py
│       ├── web_report.py
│       └── reporting.py
├── tests/                   # 단위 테스트와 리포트 회귀 테스트
├── requirements.txt
└── README.md
```

## 실행 방법

### 90일 리포트 재생성

```bash
PYTHONPATH=src python3 -m steam_success.pipeline_90d
```

생성 위치:

```text
reports/90d/
```

### 검증

```bash
PYTHONPATH=src python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests
```

## 주요 문서

- `docs/DATA_COLLECTION_RUNBOOK.md`: 데이터 수집 실행 순서와 예상 소요 시간
- `docs/DATA_COLLECTION_ATTEMPTS.md`: 수집 시도 기록, 429 리스크, 수집 규모 측정값
- `docs/ARCHITECTURE.md`: 90일 성공 예측 파이프라인 구조
- `docs/MANUAL.md`: 실행 명령과 결과 확인 위치
- `docs/OPPORTUNITY_REPORT_REDESIGN_PLAN.md`: 관측 결과와 기획 예측을 분리한 리포트 재설계 계획
