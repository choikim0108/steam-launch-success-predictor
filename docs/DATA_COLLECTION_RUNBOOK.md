# 데이터 수집 실행 준비

## 브랜치와 환경

데이터 수집 작업 브랜치는 `yongwoo`를 사용한다.

```powershell
git switch yongwoo
python -m pip install --user -r requirements.txt
$env:PYTHONPATH="src"
python -m compileall src
```

Steam Web API key는 개인 키이므로 Git에 커밋하지 않는다. 로컬 `.env`에만 둔다.

```powershell
Copy-Item .env.example .env
notepad .env
$env:STEAM_WEB_API_KEY = (Get-Content .env | Where-Object { $_ -like "STEAM_WEB_API_KEY=*" }).Split("=", 2)[1]
if ($env:STEAM_WEB_API_KEY) { "STEAM_WEB_API_KEY loaded" }
```

## 메인 수집: 2025~2026 출시 구간 appid

메인 수집 루트는 Steam 상점 검색 `Released_DESC` 최신순 크롤링이다. 2026년 게임은 최신 트렌드 대상, 2025년 게임은 트렌드와 90일 라벨 후보로 저장한다. 2024년 구간에 진입하면 중단한다.

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.search_release_window --start-year 2025 --end-year 2026 --stop-before-year 2025
```

smoke test:

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.search_release_window --start-year 2025 --end-year 2026 --stop-before-year 2025 --max-pages 2
```

2024 진입 stop 조건만 빠르게 확인할 때:

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.search_release_window --start-year 2025 --end-year 2026 --stop-before-year 2025 --start-offset 30000 --max-pages 2 --stop-pages 1
```

생성 파일:

```text
data/interim/search_release_window_appids.csv
data/raw/search_release_window/search_results_start_<n>.json
```

429 대응 원칙:

```text
기본 sleep은 1~2초로 둔다.
429 Too Many Requests가 발생하면 exponential backoff로 재시도한다.
페이지별 raw JSON을 저장한다.
누적 CSV를 매 페이지마다 갱신해 중단 후 재시작 가능하게 한다.
```

## appdetails와 리뷰 요약

1차에서 만든 2025~2026 appid 후보에 대해 appdetails와 리뷰 요약을 수집한다.

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.appdetails_for_appids --input-csv data/interim/search_release_window_appids.csv
python -m steam_success.preprocess.candidate_filter --start-year 2025 --end-year 2026
```

대량 실행용:

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.appdetails_for_appids --input-csv data/interim/search_release_window_appids.csv --flush-every 100 --sleep-seconds 1.0 --max-retries 5
```

생성 파일:

```text
data/raw/steam_appdetails.csv
data/raw/steam_review_summaries.csv
data/interim/game_candidates_2025_2026.csv
```

`appdetails_for_appids`는 중단 후 재실행을 지원한다.

```text
이미 저장된 data/raw/appdetails_<appid>.json은 재사용한다.
이미 저장된 data/raw/review_summary_<appid>.json은 재사용한다.
이전 실행에서 429 등으로 실패한 CSV row는 완료로 보지 않고 재시도한다.
data/raw/steam_appdetails.csv와 data/raw/steam_review_summaries.csv를 flush-every마다 갱신한다.
```

주의:

```text
candidate_filter는 2025~2026 게임을 모두 남긴다.
label_eligible_90d=true인 게임만 success_90d 학습 라벨을 만들 수 있다.
현재 기준일 2026-06-01에서 label 가능 기준은 release_date <= 2026-03-03이다.
```

## 리뷰 시간 지표

90일 성공 라벨을 만들려면 현재 리뷰 요약만으로는 부족하다. 우선 Steam `appreviewhistogram`의 날짜별 긍정/부정 리뷰 집계를 수집해 출시 후 7일/30일/90일 지표를 만든다. 이 경로가 90일 라벨용 메인이다.

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.review_histogram --input-csv data/interim/game_candidates_2025_2026.csv --only-label-eligible-90d --flush-every 100 --sleep-seconds 0.5
python -m steam_success.preprocess.review_windows
```

생성 파일:

```text
data/raw/steam_review_histogram.csv
data/raw/steam_review_histogram_status.csv
data/raw/review_histogram/review_histogram_<appid>.json
data/interim/game_review_windows_2025_2026.csv
```

리뷰 원문과 개별 timestamp가 필요할 때만 보조로 `review_timeline`을 제한 실행한다. 전체 2025~2026 게임에 무작정 실행하지 않는다.

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.review_timeline --appid 1903340 --max-reviews-per-game 100
```

## 검증 축: 공식 API / SteamSpy / SteamDB

공식 `IStoreService/GetAppList`는 출시일을 주지 않으므로 메인 수집이 아니라 모집단 차이 확인에 사용한다. 전체 appdetails 호출은 하지 않는다.

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.official_appids --max-apps 200000 --batch-size 50000
```

SteamSpy는 공식 데이터가 아니므로 fallback과 인기권 누락 검증에만 사용한다.

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.steamspy_appids --pages 10
```

SteamDB 연도별 출시 통계는 자동 대량 크롤링 대상이 아니라 보고서에서 외부 규모 검증 기준으로 인용한다.

## 보조/fallback 수집

상점 검색이 막히는 경우에만 공식 GetAppList 후보에서 random 표본과 high appid recent proxy 표본을 섞어 appdetails 후보를 만든다.

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.official_appids --max-apps 200000 --batch-size 50000
python -m steam_success.preprocess.appid_sample --random-size 5000 --recent-size 5000
python -m steam_success.collect.appdetails_for_appids --input-csv data/interim/appid_candidates_for_details.csv
python -m steam_success.preprocess.candidate_filter --start-year 2025 --end-year 2026
```

SteamSpy fallback:

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.steamspy_appids --pages 1
python -m steam_success.collect.appdetails_for_appids --max-apps 100
python -m steam_success.preprocess.candidate_filter --start-year 2025 --end-year 2026
```

측정 기준:

```text
공식 appid 5만 개 수집: 약 4초
공식 appid 16.8만 개 수집: 약 7초
appdetails는 후보 100개당 약 1~1.5분
실제 상점 최신순 첫 100개 appdetails/review summary 수집: 약 98.9초
0.2초 sleep에서는 appdetails 429가 많이 발생했으므로 대량 실행은 sleep 1.0초 이상을 사용한다.
SteamSpy 후보 100개 -> appdetails 필터링: 약 1~1.5분
실제 2025~2026 상점 검색 후보 28,899개 기준 전체 appdetails/review summary는 약 8~16시간 예상
```

## 수집 규모 기준

MVP:

```text
Steam 상점 검색 최신순 2025~2026 구간 appid 확보
label_eligible_90d=true 게임부터 리뷰 timeline 수집
게임당 리뷰 최대 500개
수집은 429 방지를 위해 여러 번 나눠 실행
```

권장:

```text
1차로 search_release_window smoke test
2차로 2025~2026 전체 구간 appid 확보
3차로 label_eligible_90d 게임부터 리뷰 timeline 수집
시간이 남으면 2026 최신 게임의 초기 트렌드 리뷰도 수집
```

## 다음 구현 작업

아직 필요한 전처리 작업:

```text
timestamp_created를 날짜로 변환
days_since_release 계산
reviews_7d, positive_rate_7d 생성
reviews_30d, positive_rate_30d 생성
reviews_90d, positive_rate_90d 생성
success_90d 라벨 생성
```

이 작업은 `preprocess` 모듈에 추가하는 것이 적절하다.
