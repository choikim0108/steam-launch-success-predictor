# 데이터 수집 실행 준비

## 브랜치

데이터 수집 작업 브랜치는 `yongwoo`를 사용한다.

```bash
git switch yongwoo
```

## 환경 확인

필요 패키지는 `requirements.txt`에 고정되어 있다.

```bash
python -m pip install --user -r requirements.txt
python -m compileall src
```

현재 환경에서는 Python 3.13 기준으로 수집/모델링 의존성이 설치되어 있다.

## 1차 수집: appid, 상점 정보, 리뷰 요약

기본 수집 CLI는 Steam 검색 페이지에서 appid를 모으고, appdetails와 리뷰 요약만 수집한다. 레거시 모델 학습과 리포트 생성을 피하기 위해 `steam_success.pipeline`이 아니라 `steam_success.collect.base`를 사용한다.

```bash
$env:PYTHONPATH="src"
python -m steam_success.collect.base
```

샘플 수를 제한해 먼저 확인하려면 다음처럼 실행한다.

```bash
$env:PYTHONPATH="src"
python -m steam_success.collect.base --max-apps 50
```

생성 파일:

```text
data/raw/steam_search_crawl.csv
data/raw/steam_appdetails.csv
data/raw/steam_review_summaries.csv
```

## 2차 수집: 리뷰 timestamp 타임라인

90일 성공 라벨을 만들려면 현재 리뷰 요약만으로는 부족하다. 리뷰별 `timestamp_created`와 `voted_up`을 수집해야 출시 후 7일/30일/90일 지표를 계산할 수 있다.

appid CSV를 기준으로 수집:

```bash
$env:PYTHONPATH="src"
python -m steam_success.collect.review_timeline --max-apps 50 --max-reviews-per-game 500
```

특정 appid만 테스트:

```bash
$env:PYTHONPATH="src"
python -m steam_success.collect.review_timeline --appid 1903340 --max-reviews-per-game 100
```

생성 파일:

```text
data/raw/steam_review_timeline.csv
data/raw/review_timeline/review_timeline_<appid>_page_<n>.json
```

## 수집 규모 기준

MVP:

```text
게임 300~500개
게임당 리뷰 최대 500개
```

권장:

```text
게임 800~1,500개
게임당 리뷰 최대 1,000개
```

주의:

```text
출시 후 90일이 지나지 않은 게임은 success_90d 학습 데이터에서 제외한다.
대형 히트작은 리뷰가 너무 많으므로 max_reviews_per_game 제한을 둔다.
```

## 다음 구현 작업

아직 필요한 전처리 작업:

```text
release_date_text 파싱
timestamp_created를 날짜로 변환
days_since_release 계산
reviews_7d, positive_rate_7d 생성
reviews_30d, positive_rate_30d 생성
reviews_90d, positive_rate_90d 생성
success_90d 라벨 생성
```

이 작업은 `preprocess` 모듈에 추가하는 것이 적절하다.
