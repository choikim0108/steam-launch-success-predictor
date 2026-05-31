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

## Steam Web API key 보관

Steam Web API key는 개인 키이므로 Git에 커밋하지 않는다. 로컬에서만 `.env` 파일을 만들고, 팀 공유용으로는 `.env.example`만 사용한다.

```powershell
Copy-Item .env.example .env
notepad .env
```

`.env` 안에는 다음처럼 넣는다.

```text
STEAM_WEB_API_KEY=발급받은_키
```

PowerShell에서 실행할 때는 다음처럼 현재 터미널 세션에만 환경변수로 올린다.

```powershell
$env:STEAM_WEB_API_KEY = (Get-Content .env | Where-Object { $_ -like "STEAM_WEB_API_KEY=*" }).Split("=", 2)[1]
```

확인할 때는 키 전체를 출력하지 말고 존재 여부만 확인한다.

```powershell
if ($env:STEAM_WEB_API_KEY) { "STEAM_WEB_API_KEY loaded" }
```

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

## 1.5차 수집: 공식 Steam appid 후보 기반 수집

Steam Web API key가 있으면 공식 `IStoreService/GetAppList`를 1순위 appid 후보 source로 사용한다. 이 엔드포인트는 출시일을 직접 주지는 않지만, 전체 appid 후보를 빠르게 가져올 수 있다.

```bash
$env:PYTHONPATH="src"
python -m steam_success.collect.official_appids --max-apps 200000 --batch-size 50000
python -m steam_success.preprocess.appid_sample --random-size 5000 --recent-size 5000
python -m steam_success.collect.appdetails_for_appids --input-csv data/interim/appid_candidates_for_details.csv
python -m steam_success.preprocess.candidate_filter --year 2025
```

생성 파일:

```text
data/raw/steam_official_appids.csv
data/interim/appid_candidates_for_details.csv
data/raw/steam_appdetails.csv
data/raw/steam_review_summaries.csv
data/interim/game_candidates_2025.csv
```

측정 기준:

```text
공식 appid 5만 개 수집: 약 4초
공식 appid 16.8만 개 수집: 약 7초
appdetails는 여전히 후보 100개당 약 1~1.5분
```

주의:

```text
공식 GetAppList에는 release date가 없으므로, 2025년 게임 여부는 appdetails 이후에만 확정할 수 있다.
전체 16만 개를 모두 appdetails로 호출하면 시간이 너무 오래 걸린다.
따라서 random 표본과 high appid recent proxy 표본을 섞어 appdetails 후보를 만든다.
```

## 1.6차 fallback: SteamSpy appid 후보 기반 수집

Steam 공식 전체 appid API가 접근되지 않거나 API key가 없을 때는 SteamSpy `request=all&page=N`을 appid 후보 목록으로 사용한다. 이 방식은 전체 Steam 모집단의 완전한 대체는 아니지만, 검색 페이지보다 많은 appid 후보를 빠르게 확보할 수 있다.

```bash
$env:PYTHONPATH="src"
python -m steam_success.collect.steamspy_appids --pages 1
python -m steam_success.collect.appdetails_for_appids --max-apps 100
python -m steam_success.preprocess.candidate_filter --year 2025
```

생성 파일:

```text
data/raw/steamspy_appids.csv
data/raw/steam_appdetails.csv
data/raw/steam_review_summaries.csv
data/interim/game_candidates_2025.csv
```

측정 기준:

```text
후보 100개 appdetails 수집 + 2025 필터링: 약 1~1.5분
후보 5000개 appdetails 수집 + 2025 필터링: 약 50~75분 예상
후보 10000개 appdetails 수집 + 2025 필터링: 약 100~150분 예상
```

## 2차 수집: 리뷰 timestamp 타임라인

90일 성공 라벨을 만들려면 현재 리뷰 요약만으로는 부족하다. 리뷰별 `timestamp_created`와 `voted_up`을 수집해야 출시 후 7일/30일/90일 지표를 계산할 수 있다.

appid CSV를 기준으로 수집:

```bash
$env:PYTHONPATH="src"
python -m steam_success.collect.review_timeline --max-apps 50 --max-reviews-per-game 500
```

2025년 후보 CSV를 기준으로 수집:

```bash
$env:PYTHONPATH="src"
python -m steam_success.collect.review_timeline --input-csv data/interim/game_candidates_2025.csv --max-reviews-per-game 500
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
SteamSpy 후보 5000개
2025년 게임 후보 약 200~300개 예상
게임당 리뷰 최대 500개
총 수집 시간 약 2~3시간 예상
```

권장:

```text
SteamSpy 후보 10000개
2025년 게임 후보 약 400~600개 예상
게임당 리뷰 최대 500~1,000개
총 수집 시간 약 4~6시간 예상
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
