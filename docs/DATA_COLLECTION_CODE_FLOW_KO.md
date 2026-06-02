# 데이터 수집 코드 사용 흐름

작성 기준: 2026-06-01 현재 `yongwoo` 브랜치

## 목적

이 문서는 "무슨 데이터를 모으는가"보다 **현재 코드를 어떤 명령으로 실행하고, 그 코드가 내부에서 어떤 API를 호출해 어떤 파일을 만드는가**를 설명한다.

## 전체 실행 순서

```text
1. search_release_window
   Steam 상점 검색 최신순으로 2025~2026 appid 후보 수집

2. appdetails_for_appids
   appid별 상점 상세 정보와 현재 리뷰 요약 수집

3. candidate_filter
   실제 게임 + 2025~2026 출시작만 필터링

4. review_histogram
   label 가능 게임의 날짜별 긍정/부정 리뷰 집계 수집

5. review_windows
   7일/30일/90일 리뷰 지표와 success_90d 생성

6. review_timeline
   리뷰 원문과 개별 timestamp가 필요할 때만 보조 실행
```

## 0. 실행 전 준비

PowerShell에서 repo 루트 기준으로 실행한다.

```powershell
cd C:\Users\asdf7\Desktop\게임데이터마이닝\steam-launch-success-predictor
$env:PYTHONPATH="src"
```

`PYTHONPATH=src`를 넣는 이유:

`steam_success` 패키지가 `src/steam_success` 아래에 있으므로, PowerShell에서 모듈 실행 시 Python이 이 패키지를 찾을 수 있게 해야 한다.

## 1. 2025~2026 appid 후보 수집

실행 명령:

```powershell
python -m steam_success.collect.search_release_window --start-year 2025 --end-year 2026 --stop-before-year 2025
```

관련 코드:

```text
src/steam_success/collect/search_release_window.py
```

코드 흐름:

```text
main()
-> collect_release_window()
-> _fetch_search_page()
-> _parse_rows()
-> CSV와 raw JSON 저장
```

호출하는 Steam URL:

```text
https://store.steampowered.com/search/results/
```

주요 요청 옵션:

| 옵션 | 의미 |
| --- | --- |
| `sort_by=Released_DESC` | 최신 출시순 |
| `category1=998` | Steam 앱 중 게임 중심 검색 |
| `count=100` | 한 번에 100개씩 가져오기 |
| `start=<n>` | 검색 결과 offset |
| `cc=US` | 미국 기준 상점 정보 |
| `l=english` | 영어 기준 응답 |

저장 파일:

```text
data/interim/search_release_window_appids.csv
data/raw/search_release_window/search_results_start_<n>.json
```

이 코드가 하는 일:

1. Steam 검색 결과를 최신 출시순으로 100개씩 가져온다.
2. HTML 안의 게임 row에서 appid, 이름, 출시일, 가격을 뽑는다.
3. 출시 연도가 2026이면 `2026_trend`, 2025면 `2025_trend_label_candidate`로 표시한다.
4. 2024년 페이지만 연속으로 나오면 2025~2026 구간이 끝났다고 보고 멈춘다.
5. 매 페이지마다 CSV를 갱신하므로 중간에 끊겨도 이어서 볼 수 있다.

현재 결과:

```text
data/interim/search_release_window_appids.csv
총 28,899개 appid 후보
```

## 2. 상점 상세 정보와 현재 리뷰 요약 수집

현재 실행 중인 명령:

```powershell
python -u -m steam_success.collect.appdetails_for_appids --input-csv data/interim/search_release_window_appids.csv --flush-every 100 --sleep-seconds 1.0 --max-retries 5
```

관련 코드:

```text
src/steam_success/collect/appdetails_for_appids.py
```

코드 흐름:

```text
main()
-> run()
-> _load_appids()
-> _load_existing_rows()
-> appid 반복
   -> _collect_appdetails()
   -> _collect_review_summary()
-> _write_rows()
```

### 2-1. appdetails 수집

호출하는 Steam URL:

```text
https://store.steampowered.com/api/appdetails
```

요청 예시:

```text
appids=<appid>
cc=US
l=english
```

저장 파일:

```text
data/raw/appdetails_<appid>.json
data/raw/steam_appdetails.csv
```

이 코드가 가져오는 것:

| 데이터 | 의미 |
| --- | --- |
| 게임 이름 | 리포트 표시용 |
| 출시일 | 2025/2026 필터링과 90일 가능 여부 계산 |
| 장르 | 트렌드 분석과 모델 feature |
| 카테고리 | 싱글플레이, 컨트롤러 지원 등 기능 feature |
| 가격 | 가격 비교와 모델 feature |
| 플랫폼 | Windows/Mac/Linux 지원 여부 |
| 지원 언어 | 언어 수 feature 생성 재료 |
| Metacritic 점수 | 있으면 현재 평가 비교용 |

### 2-2. 현재 리뷰 요약 수집

호출하는 Steam URL:

```text
https://store.steampowered.com/appreviews/<appid>
```

요청 옵션:

```text
json=1
filter=summary
language=all
purchase_type=all
num_per_page=0
```

저장 파일:

```text
data/raw/review_summary_<appid>.json
data/raw/steam_review_summaries.csv
```

이 코드가 가져오는 것:

| 데이터 | 의미 |
| --- | --- |
| `total_reviews` | 현재 누적 리뷰 수 |
| `total_positive` | 현재 누적 긍정 리뷰 수 |
| `total_negative` | 현재 누적 부정 리뷰 수 |
| `positive_rate` | 현재 누적 긍정률 |
| `review_score_desc` | Very Positive 같은 Steam 리뷰 등급 |

주의:

이 값은 "현재 누적값"이다. 모델의 90일 정답 라벨은 이 값만으로 만들지 않고, 뒤에서 날짜별 리뷰 집계를 이용해 다시 만든다.

### 2-3. 왜 중간에 끊겨도 이어서 되는가

`appdetails_for_appids.py`는 이미 저장된 raw JSON과 CSV를 먼저 확인한다.

```text
이미 data/raw/appdetails_<appid>.json 이 있으면 다시 호출하지 않음
이미 data/raw/review_summary_<appid>.json 이 있으면 다시 호출하지 않음
CSV에서 success=true인 row는 완료로 보고 건너뜀
flush-every마다 CSV를 다시 저장함
```

그래서 수집이 중간에 끊겨도 같은 명령을 다시 실행하면 기존 결과를 재사용하며 이어서 진행한다.

## 3. 2025~2026 게임 후보 필터링

실행 명령:

```powershell
python -m steam_success.preprocess.candidate_filter --start-year 2025 --end-year 2026
```

관련 코드:

```text
src/steam_success/preprocess/candidate_filter.py
```

코드 흐름:

```text
main()
-> run()
-> filter_game_candidates()
-> parse_release_date()
-> CSV 저장
```

입력 파일:

```text
data/raw/steam_appdetails.csv
```

출력 파일:

```text
data/interim/game_candidates_2025_2026.csv
```

필터 조건:

```text
detail_success == true
type == "game"
coming_soon == false
release_year >= 2025
release_year <= 2026
```

추가로 만드는 값:

| 컬럼 | 의미 |
| --- | --- |
| `release_year` | 출시 연도 |
| `release_date` | 날짜형 출시일 |
| `label_eligible_90d` | 90일 성공 라벨을 만들 수 있는지 여부 |

현재 기준:

```text
release_date <= 2026-03-03 이면 label_eligible_90d = true
```

## 4. 날짜별 리뷰 집계 수집

90일 성공 라벨용 메인 경로다.

실행 명령:

```powershell
python -m steam_success.collect.review_histogram --input-csv data/interim/game_candidates_2025_2026.csv --only-label-eligible-90d --flush-every 100 --sleep-seconds 0.5
```

관련 코드:

```text
src/steam_success/collect/review_histogram.py
```

코드 흐름:

```text
main()
-> run()
-> _load_appids()
-> _collect_one()
-> _request_json()
-> _rows_from_payload()
-> histogram CSV와 status CSV 저장
```

호출하는 Steam URL:

```text
https://store.steampowered.com/appreviewhistogram/<appid>
```

저장 파일:

```text
data/raw/review_histogram/review_histogram_<appid>.json
data/raw/steam_review_histogram.csv
data/raw/steam_review_histogram_status.csv
```

이 코드가 가져오는 것:

| 데이터 | 의미 |
| --- | --- |
| `bucket_date_unix` | 리뷰 집계 날짜 |
| `recommendations_up` | 해당 날짜 구간의 긍정 리뷰 수 |
| `recommendations_down` | 해당 날짜 구간의 부정 리뷰 수 |
| `recommendations_total` | 긍정+부정 리뷰 수 |
| `histogram_success` | 해당 appid 수집 성공 여부 |
| `rollup_rows` | 집계 row 수 |

왜 이걸 쓰는가:

90일 라벨에는 리뷰 본문 전체가 필요하지 않다. 날짜별로 긍정/부정 리뷰가 몇 개 쌓였는지만 있으면 출시 후 7일, 30일, 90일 지표를 만들 수 있다. 그래서 `review_timeline`보다 가볍다.

## 5. 7일/30일/90일 지표 생성

실행 명령:

```powershell
python -m steam_success.preprocess.review_windows
```

관련 코드:

```text
src/steam_success/preprocess/review_windows.py
```

코드 흐름:

```text
main()
-> run()
-> build_review_windows()
-> bucket_date_unix를 날짜로 변환
-> release_date와 비교해 days_since_release 계산
-> 7일/30일/90일 누적 리뷰 수와 긍정률 생성
-> success_90d 생성
-> CSV 저장
```

입력 파일:

```text
data/interim/game_candidates_2025_2026.csv
data/raw/steam_review_histogram.csv
```

출력 파일:

```text
data/interim/game_review_windows_2025_2026.csv
```

생성되는 주요 값:

| 컬럼 | 의미 |
| --- | --- |
| `reviews_7d` | 출시 후 7일 누적 리뷰 수 |
| `positive_rate_7d` | 출시 후 7일 긍정률 |
| `reviews_30d` | 출시 후 30일 누적 리뷰 수 |
| `positive_rate_30d` | 출시 후 30일 긍정률 |
| `reviews_90d` | 출시 후 90일 누적 리뷰 수 |
| `positive_rate_90d` | 출시 후 90일 긍정률 |
| `success_90d` | 90일 기준 성공 여부 |

성공 라벨 생성 조건:

```text
success_90d =
label_eligible_90d == true
AND reviews_90d >= SETTINGS.success_review_threshold
AND positive_rate_90d >= SETTINGS.success_positive_rate_threshold
```

현재 설정 기준:

```text
reviews_90d >= 500
positive_rate_90d >= 0.80
```

## 6. 리뷰 원문이 필요할 때만 보조 수집

실행 예시:

```powershell
python -m steam_success.collect.review_timeline --appid 1903340 --max-reviews-per-game 100
```

관련 코드:

```text
src/steam_success/collect/review_timeline.py
src/steam_success/collect/steam.py
```

코드 흐름:

```text
review_timeline.py main()
-> run()
-> fetch_review_timeline()
-> appreviews API를 cursor로 페이지 이동
-> 리뷰 원문과 timestamp 저장
```

호출하는 Steam URL:

```text
https://store.steampowered.com/appreviews/<appid>
```

저장 파일:

```text
data/raw/review_timeline/review_timeline_<appid>_page_<n>.json
data/raw/steam_review_timeline.csv
```

이 코드가 가져오는 것:

| 데이터 | 의미 |
| --- | --- |
| `review_text` | 리뷰 본문 |
| `voted_up` | 긍정/부정 여부 |
| `timestamp_created` | 리뷰 작성 시각 |
| `playtime_hours` | 작성자 플레이 시간 |
| `votes_up` | 도움이 됐다는 투표 수 |

언제 쓰는가:

```text
리뷰 키워드 분석
유사 게임의 긍정/부정 피드백 추출
실제 리뷰 문장 예시 확인
```

언제 안 쓰는가:

```text
90일 성공 라벨만 만들 때는 굳이 전체 게임에 돌리지 않는다.
그 목적은 review_histogram이 더 가볍게 처리한다.
```

## 지금 실제로 돌아가는 단계

현재 실행 중인 것은 2단계다.

```text
appdetails_for_appids
-> search_release_window_appids.csv의 appid를 하나씩 읽음
-> appdetails API 호출
-> appreviews summary 호출
-> raw JSON 저장
-> steam_appdetails.csv / steam_review_summaries.csv 갱신
```

현재 단계가 끝나거나 충분한 개수가 쌓이면 다음 순서로 진행한다.

```powershell
$env:PYTHONPATH="src"
python -m steam_success.preprocess.candidate_filter --start-year 2025 --end-year 2026
python -m steam_success.collect.review_histogram --input-csv data/interim/game_candidates_2025_2026.csv --only-label-eligible-90d --flush-every 100 --sleep-seconds 0.5
python -m steam_success.preprocess.review_windows
```

## 각 코드 파일의 역할

| 파일 | 역할 |
| --- | --- |
| `collect/search_release_window.py` | Steam 상점 최신순 검색에서 2025~2026 appid 후보 수집 |
| `collect/appdetails_for_appids.py` | appid별 상점 정보와 현재 리뷰 요약 수집 |
| `preprocess/candidate_filter.py` | 실제 2025~2026 출시 게임만 남김 |
| `collect/review_histogram.py` | 날짜별 긍정/부정 리뷰 집계 수집 |
| `preprocess/review_windows.py` | 7일/30일/90일 리뷰 지표와 `success_90d` 생성 |
| `collect/review_timeline.py` | 리뷰 원문과 개별 timestamp 보조 수집 |
| `collect/official_appids.py` | 공식 appid 목록 검증용 수집 |
| `collect/steamspy_appids.py` | SteamSpy 후보 검증/fallback 수집 |

## 중단 후 재시작 방식

현재 수집 코드는 장시간 실행을 전제로 한다.

```text
raw JSON이 있으면 재사용
성공 CSV row가 있으면 완료로 취급
flush_every마다 CSV 저장
429가 나오면 backoff 후 재시도
실패 row는 나중에 다시 시도 가능
```

그래서 긴 수집이 중간에 멈춰도 같은 명령을 다시 실행하면 처음부터 전부 다시 받지 않고 이어서 진행한다.
