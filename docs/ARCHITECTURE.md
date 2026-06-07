# 90일 성공 예측 파이프라인 아키텍처

## 목적

2025~2026 Steam 출시 게임의 상점 정보와 출시 초기 리뷰 데이터를 수집해 최신 트렌드를 분석하고, 출시 후 90일 성공 가능성을 예측한다. 현재 누적 리뷰 기준으로 만든 초기 작동 모델은 `legacy/current_snapshot/`에 보존했고, 신규 작업은 `success_90d` 기준으로 진행한다.

현재 기준일은 2026-06-01이다. `success_90d` 학습 라벨은 `release_date <= 2026-03-03` 게임에만 만들고, 그 이후 출시된 2026 게임은 최신 트렌드와 예측 대상에만 포함한다.

상세 UX 설계와 상태 점검 기록은 `docs/reference/`에 있으며, 실제 구현 판단은 이 문서와 `DATA_COLLECTION_RUNBOOK.md`를 우선한다.

## 데이터 흐름

```text
Steam 상점 검색 Released_DESC 크롤링
        |
        v
2025~2026 release window appid 수집
        |
        v
Steam appdetails API
        |
        v
상점 feature / label_eligible_90d 생성
        |
        v
Steam Reviews API 페이지네이션
        |
        v
리뷰별 timestamp_created / voted_up 수집
        |
        v
7일/30일/90일 리뷰 지표 생성
        |
        v
success_90d 라벨 생성
        |
        v
분류 모델 학습 및 평가
        |
        v
EDA / 유사 게임 / 리뷰 키워드 / 리포트
```

## 현재 모듈 상태

```text
src/steam_success/collect/steam.py
- Steam 검색 페이지 appid 수집
- appdetails 수집
- 리뷰 요약 수집
- 리뷰 텍스트 일부 수집
- 리뷰 timeline 페이지네이션 수집 준비

src/steam_success/collect/review_timeline.py
- appid 목록 또는 단일 appid 기준 리뷰 timestamp 수집 CLI

src/steam_success/preprocess/dataset.py
- 아직 현재 누적 total_reviews/positive_rate 기준 success 생성
- 다음 작업에서 success_90d 기준으로 교체 필요

src/steam_success/features/build_features.py
- 아직 success 컬럼을 y로 사용
- 다음 작업에서 success_90d와 7일 feature 기준으로 교체 필요

src/steam_success/models/train.py
- Logistic Regression, Random Forest 학습/평가
- y 컬럼 교체 후 재사용 가능
```

## 신규 전처리 목표

리뷰 타임라인과 appdetails를 병합해 다음 컬럼을 만든다.

```text
release_date
reviews_7d
positive_rate_7d
reviews_30d
positive_rate_30d
reviews_90d
positive_rate_90d
review_velocity_7d
success_90d
```

## 모델 입력과 제외 기준

모델 입력으로 사용할 수 있는 값:

```text
가격
장르/태그/카테고리
지원 언어 수
플랫폼 수
싱글/멀티 여부
컨트롤러 지원 여부
도전과제 지원 여부
출시 7일 리뷰 수
출시 7일 긍정률
출시 7일 리뷰 증가 속도
```

모델 입력에서 제외할 값:

```text
출시 90일 리뷰 수
출시 90일 긍정률
현재 전체 리뷰 수
현재 긍정률
현재 판매량 추정치
현재 동접자
현재 Metacritic 점수
웹진 현재 검색 점수
```

## 보조 분석 위치

공식 GetAppList, SteamSpy, SteamDB, 웹진 관심도, Metacritic/OpenCritic, 현재 동접자는 예측 모델의 핵심 입력이 아니라 현재 성과 비교와 사용자 설명용 보조 지표로 둔다.

```text
official_population_gap
steamspy_popular_overlap
steamdb_yearly_release_count
sales_proxy_score
critic_score
attention_score
activity_score
```

## 산출물 원칙

신규 산출물은 기존 현재 누적 기준 결과와 파일명이 섞이지 않도록 한다.

```text
data/raw/steam_review_timeline.csv
data/interim/search_release_window_appids.csv
data/interim/game_candidates_2025_2026.csv
data/interim/game_review_windows_2025_2026.csv
data/processed/modeling_dataset_90d.csv
reports/90d/model_metrics.json
reports/90d/model_metrics.csv
reports/90d/predictions.csv
reports/90d/RUN_SUMMARY.md
reports/90d/market_insight_site.html
models/steam_success_90d_model.joblib
```
