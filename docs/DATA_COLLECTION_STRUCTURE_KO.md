# 데이터 수집 구조 정리

작성 기준: 2026-06-01 현재 `yongwoo` 브랜치

## 한 줄 요약

현재 수집 구조는 **2025~2026년에 Steam에 출시된 게임을 최신순으로 모은 뒤, 상점 정보와 리뷰 정보를 붙여서 최신 트렌드 분석과 90일 성공 예측에 쓰는 구조**다.

```text
Steam 상점 최신순 검색
-> 2025~2026 appid 후보
-> appdetails 상점 정보
-> 리뷰 요약
-> 2025~2026 게임 후보 필터링
-> 날짜별 리뷰 집계 수집
-> 7일/30일/90일 리뷰 지표
-> success_90d 라벨과 모델 학습 데이터
```

## 현재 진행 상태

현재 실행 중인 수집:

```powershell
python -u -m steam_success.collect.appdetails_for_appids --input-csv data/interim/search_release_window_appids.csv --flush-every 100 --sleep-seconds 1.0 --max-retries 5
```

현재 확인된 산출물:

| 파일 | 현재 상태 | 의미 |
| --- | ---: | --- |
| `data/interim/search_release_window_appids.csv` | 28,899행 | 2025~2026 출시 후보 appid 수집 완료 |
| `data/raw/steam_appdetails.csv` | 28,899행 | 상점 상세 정보 수집 완료 |
| `data/raw/steam_review_summaries.csv` | 28,899행 | 전체 리뷰 수/긍정률 요약 수집 완료 |
| `data/interim/game_candidates_2025_2026.csv` | 28,627행 | 정제된 2025~2026 게임 후보 |
| `data/raw/steam_review_histogram.csv` | 264,361행 | 날짜별 리뷰 집계 수집 완료 |
| `data/raw/steam_review_histogram_status.csv` | 22,504행 | 90일 라벨 가능 게임 히스토그램 수집 상태, 에러 0 |
| `data/interim/game_review_windows_2025_2026.csv` | 28,627행 | 7일/30일/90일 리뷰 지표와 `success_90d` 라벨 |
| `data/raw/steam_review_timeline.csv` | 아직 없음 | 리뷰 원문이 필요할 때만 보조 수집 |

주의:

`appdetails` 수집이 끝나거나 일정 구간까지 쌓이면 `candidate_filter`를 다시 실행해야 `game_candidates_2025_2026.csv`가 최신 상태가 된다.

## 1단계: 2025~2026 appid 후보 수집

실행 코드:

```powershell
python -m steam_success.collect.search_release_window --start-year 2025 --end-year 2026 --stop-before-year 2025
```

생성 파일:

```text
data/interim/search_release_window_appids.csv
data/raw/search_release_window/search_results_start_<n>.json
```

역할:

Steam 상점 검색을 `Released_DESC` 최신순으로 내려가며 2026년 최신 게임부터 2025년 게임까지 appid 후보를 모은다. 2024년 구간에 들어가면 멈춘다.

주요 데이터 설명:

| 컬럼 | 한글 설명 | 쓰임 |
| --- | --- | --- |
| `appid` | Steam 게임 고유 번호 | 모든 데이터 병합 기준 |
| `search_name` | 검색 결과에 나온 게임 이름 | 사람이 확인할 때 사용 |
| `search_release_text` | 검색 결과의 출시일 문자열 | 출시 연도 1차 판단 |
| `search_release_year` | 출시 연도 | 2025/2026 구분 |
| `release_year_bucket` | 수집 범위 안/밖 연도 구분 | 2025~2026 필터링 확인 |
| `release_window_role` | 이 게임의 수집 목적 분류 | 2026 트렌드인지, 2025 라벨 후보인지 구분 |
| `search_price_text` | 검색 결과의 가격 문자열 | 참고용 가격 정보 |
| `start` | Steam 검색 페이지 offset | 어디서 수집됐는지 추적 |
| `source_url` | 실제 호출한 검색 URL | 재현/검증용 |

`release_window_role` 의미:

| 값 | 의미 |
| --- | --- |
| `2026_trend` | 2026년 최신 트렌드 분석 대상 |
| `2025_trend_label_candidate` | 2025년 트렌드 분석 + 90일 라벨 후보 |
| `out_of_range` | 2025~2026 밖이라 메인 분석에서는 제외 |
| `unknown` | 출시 연도를 검색 결과에서 못 읽은 경우 |

## 2단계: appdetails 상점 정보 수집

실행 코드:

```powershell
python -m steam_success.collect.appdetails_for_appids --input-csv data/interim/search_release_window_appids.csv --flush-every 100 --sleep-seconds 1.0 --max-retries 5
```

생성 파일:

```text
data/raw/appdetails_<appid>.json
data/raw/steam_appdetails.csv
```

역할:

각 appid에 대해 Steam Store appdetails API를 호출해서 게임의 상점 정보를 가져온다. 모델 입력 feature와 추천/비교 기준의 기본 데이터가 된다.

주요 데이터 설명:

| 컬럼 | 한글 설명 | 쓰임 |
| --- | --- | --- |
| `appid` | Steam 게임 고유 번호 | 병합 기준 |
| `detail_success` | 상점 정보 수집 성공 여부 | 실패 데이터 제외/재시도 판단 |
| `name` | 게임 이름 | 리포트 표시 |
| `type` | 앱 종류 | `game`만 분석 대상으로 사용 |
| `is_free` | 무료 게임 여부 | 가격 feature |
| `required_age` | 연령 제한 | 상점 feature |
| `release_date_text` | Steam 상점 출시일 | 출시 연도/90일 가능 여부 판단 |
| `coming_soon` | 출시 예정 여부 | 아직 출시 안 된 게임 제외 |
| `price_initial_usd` | 할인 전 가격 | 가격 비교 |
| `price_final_usd` | 현재 가격 | 가격 비교 |
| `discount_percent` | 할인율 | 현재 판매 상태 참고 |
| `developers` | 개발사 | 참고/표시용 |
| `publishers` | 배급사 | 참고/표시용 |
| `genres` | 장르 | 추천/트렌드/모델 feature |
| `categories` | 지원 기능 | 컨트롤러, 싱글플레이 등 feature |
| `platform_windows` | Windows 지원 | 플랫폼 feature |
| `platform_mac` | Mac 지원 | 플랫폼 feature |
| `platform_linux` | Linux 지원 | 플랫폼 feature |
| `metacritic_score` | Steam appdetails에 포함된 메타크리틱 점수 | 있으면 현재 평가 비교용 |
| `recommendations_total` | Steam 추천 수 | 보조 인기 지표 |
| `supported_languages_raw` | 지원 언어 원문 | 언어 수 feature 생성 재료 |
| `detail_error` | 수집 실패 사유 | 재시도/디버깅용 |

## 3단계: 리뷰 요약 수집

실행 코드:

`appdetails_for_appids`가 appdetails와 함께 자동으로 수집한다.

생성 파일:

```text
data/raw/review_summary_<appid>.json
data/raw/steam_review_summaries.csv
```

역할:

각 게임의 현재 누적 리뷰 수와 긍정률을 빠르게 가져온다. 전체 성과 비교에는 쓸 수 있지만, 시간별 90일 예측 라벨을 만들려면 다음 단계의 리뷰 timestamp가 필요하다.

주요 데이터 설명:

| 컬럼 | 한글 설명 | 쓰임 |
| --- | --- | --- |
| `appid` | Steam 게임 고유 번호 | 병합 기준 |
| `review_success` | 리뷰 요약 수집 성공 여부 | 실패 데이터 제외/재시도 판단 |
| `review_score` | Steam 내부 리뷰 점수 코드 | 참고용 |
| `review_score_desc` | Very Positive 같은 리뷰 등급 문구 | 리포트 표시 |
| `total_reviews` | 현재 누적 리뷰 수 | 현재 성과 비교 |
| `total_positive` | 현재 누적 긍정 리뷰 수 | 현재 긍정률 계산 |
| `total_negative` | 현재 누적 부정 리뷰 수 | 현재 긍정률 계산 |
| `positive_rate` | 현재 누적 긍정률 | 현재 성과 비교 |

중요:

`total_reviews`와 `positive_rate`는 현재 누적값이다. 90일 성공 예측 모델의 정답 라벨로 바로 쓰면 안 되고, 리뷰 timestamp를 이용해 출시 후 90일 기준으로 다시 계산해야 한다.

## 4단계: 2025~2026 게임 후보 필터링

실행 코드:

```powershell
python -m steam_success.preprocess.candidate_filter --start-year 2025 --end-year 2026
```

생성 파일:

```text
data/interim/game_candidates_2025_2026.csv
```

역할:

appdetails 결과 중에서 실제 게임이고, 출시 예정이 아니며, 출시 연도가 2025~2026인 항목만 남긴다. 이후 리뷰 timestamp 수집과 모델링의 입력 목록이 된다.

추가 데이터 설명:

| 컬럼 | 한글 설명 | 쓰임 |
| --- | --- | --- |
| `release_year` | 출시 연도 | 2025/2026 분석 구분 |
| `release_date` | 날짜형 출시일 | 출시 후 경과일 계산 |
| `label_eligible_90d` | 90일 성공 라벨 생성 가능 여부 | 모델 학습 대상 구분 |

`label_eligible_90d` 기준:

현재 기준일이 2026-06-01이므로, 출시 후 90일이 지난 게임만 라벨을 만들 수 있다.

```text
release_date <= 2026-03-03 -> label_eligible_90d = true
release_date >= 2026-03-04 -> 트렌드/예측 대상이지만 학습 라벨은 아직 불가
```

## 5단계: 날짜별 리뷰 집계 수집

실행 코드:

```powershell
python -m steam_success.collect.review_histogram --input-csv data/interim/game_candidates_2025_2026.csv --only-label-eligible-90d --flush-every 100 --sleep-seconds 0.5
python -m steam_success.preprocess.review_windows
```

생성 파일:

```text
data/raw/review_histogram/review_histogram_<appid>.json
data/raw/steam_review_histogram.csv
data/raw/steam_review_histogram_status.csv
data/interim/game_review_windows_2025_2026.csv
```

역할:

Steam `appreviewhistogram`에서 날짜별 긍정/부정 리뷰 집계를 가져온다. 이 데이터로 출시 후 7일, 30일, 90일 리뷰 수와 긍정률을 계산한다.

주요 데이터 설명:

| 컬럼 | 한글 설명 | 쓰임 |
| --- | --- | --- |
| `appid` | Steam 게임 고유 번호 | 병합 기준 |
| `bucket_date_unix` | 리뷰 집계 날짜 | 출시 후 며칠째인지 계산 |
| `recommendations_up` | 해당 날짜 구간의 긍정 리뷰 수 | 긍정 리뷰 누적 계산 |
| `recommendations_down` | 해당 날짜 구간의 부정 리뷰 수 | 부정 리뷰 누적 계산 |
| `recommendations_total` | 긍정+부정 리뷰 수 | 전체 리뷰 누적 계산 |
| `histogram_success` | 날짜별 집계 수집 성공 여부 | 실패 데이터 제외/재시도 판단 |
| `rollup_rows` | 해당 appid에서 얻은 집계 row 수 | 수집 품질 확인 |

보조 수집:

리뷰 본문과 개별 작성 시각이 필요하면 `review_timeline`을 제한적으로 실행한다. 이 경로는 리뷰 키워드/피드백 분석용이며, 90일 성공 라벨용 메인은 `review_histogram`이다.

```powershell
python -m steam_success.collect.review_timeline --appid 1903340 --max-reviews-per-game 100
```

## 6단계: 이후 전처리에서 만들 데이터

아직 별도 전처리 코드가 추가로 필요하다.

만들어야 할 지표:

| 지표 | 한글 설명 | 쓰임 |
| --- | --- | --- |
| `reviews_7d` | 출시 후 7일 안에 쌓인 리뷰 수 | 초기 관심도 feature |
| `positive_rate_7d` | 출시 후 7일 긍정률 | 초기 반응 feature |
| `reviews_30d` | 출시 후 30일 리뷰 수 | 중기 반응 비교 |
| `positive_rate_30d` | 출시 후 30일 긍정률 | 중기 반응 비교 |
| `reviews_90d` | 출시 후 90일 리뷰 수 | 성공 라벨 재료 |
| `positive_rate_90d` | 출시 후 90일 긍정률 | 성공 라벨 재료 |
| `success_90d` | 90일 기준 성공 여부 | 모델 학습 정답 |

기본 성공 라벨:

```text
success_90d =
reviews_90d >= 500
AND positive_rate_90d >= 0.80
```

## 데이터별 역할 구분

| 데이터 | 예측 모델 입력 | 비교/리포트 | 설명 |
| --- | --- | --- | --- |
| 상점 정보 | 사용 | 사용 | 가격, 장르, 태그, 언어, 플랫폼 같은 출시 시점 feature |
| 출시 7일 리뷰 지표 | 사용 | 사용 | 예측 시점에 가까운 초기 반응 |
| 출시 30일 리뷰 지표 | 선택 | 사용 | 중간 성과 비교용 |
| 출시 90일 리뷰 지표 | 정답 라벨 | 사용 | 성공 여부 판단 기준 |
| 현재 누적 리뷰 요약 | 직접 입력 금지 | 사용 | 현재 성과 확인용 |
| Metacritic 점수 | 제한적 | 사용 | appdetails에 있으면 평가 비교용 |
| SteamSpy owners | 사용 안 함 | 검증/보조 | 공식 데이터가 아니라 메인 수집 아님 |
| SteamDB 연도 통계 | 사용 안 함 | 검증 | 수집 규모가 이상하지 않은지 외부 기준으로 확인 |

## 왜 현재 누적값을 모델에 바로 넣으면 안 되는가

이 프로젝트는 "예측"이 목적이다. 그래서 예측 시점에 알 수 없던 정보를 모델 입력으로 넣으면 안 된다.

예:

```text
출시 7일 시점에 90일 성공을 예측한다면
입력 X: 상점 정보 + 출시 7일 리뷰 지표
정답 y: 출시 90일 리뷰 수와 긍정률로 만든 success_90d
```

현재 누적 리뷰 수, 현재 긍정률, 현재 동접자 같은 값은 이미 결과에 가까운 정보다. 이런 값은 모델 입력이 아니라 리포트의 현재 성과 비교용으로 둔다.

## 다음 작업 순서

1. 현재 실행 중인 `appdetails_for_appids`가 충분히 진행될 때까지 둔다.
2. 중간 확인이 필요하면 `data/raw/steam_appdetails.csv`와 `data/raw/steam_review_summaries.csv` 행 수를 본다.
3. 일정 구간 수집 후 `candidate_filter`를 다시 실행한다.
4. `label_eligible_90d=true`인 게임부터 `review_histogram`을 수집한다.
5. `review_windows`로 7일/30일/90일 지표와 `success_90d`를 만든다.
6. 리뷰 텍스트 피드백이 필요할 때만 `review_timeline`을 제한 실행한다.

## 빠른 확인 명령

```powershell
$env:PYTHONPATH="src"
python -m steam_success.preprocess.candidate_filter --start-year 2025 --end-year 2026
```

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Select-Object ProcessId,CommandLine,CreationDate
```

```powershell
@'
import pandas as pd
for path in [
    "data/interim/search_release_window_appids.csv",
    "data/raw/steam_appdetails.csv",
    "data/raw/steam_review_summaries.csv",
    "data/interim/game_candidates_2025_2026.csv",
]:
    df = pd.read_csv(path)
    print(path, len(df), list(df.columns))
'@ | python -
```
