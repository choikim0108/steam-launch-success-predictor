# 데이터 수집 조사 및 시도 기록

## 목표 변경

현재 목표는 2025~2026 Steam 출시 게임을 기준으로 최신 트렌드를 분석하고, 출시 후 90일이 지난 게임에 대해서만 `success_90d` 학습 라벨을 만드는 것이다.

```text
2025~2026 Steam 출시 구간
-> appdetails로 출시일/상점 feature 확정
-> Reviews API timestamp 수집
-> 7일/30일/90일 리뷰 지표
-> label_eligible_90d 게임만 success_90d 생성
```

현재 기준일은 2026-06-01이다.

```text
학습 라벨 가능: release_date <= 2026-03-03
트렌드/예측 전용: release_date >= 2026-03-04
```

## 1차: Steam 상점 검색 최신순 조사

Steam Store `search/results` endpoint를 `Released_DESC`, `category1=998`, `count=100` 기준으로 조사했다.

```text
total_count=113,180
start=0      -> May 31, 2026
start=10,000 -> Dec 18, 2025
start=20,000 -> Jun 25, 2025
start=28,000 -> Jan 18, 2025
start=30,000 -> Dec 4, 2024
```

판단:

```text
상점 검색 최신순으로 내려가면 2025~2026 출시 구간을 직접 겨냥할 수 있다.
대략 start=0~30,000 범위가 2026~2025 구간이다.
이 방식이 현재 프로젝트의 메인 수집 루트에 가장 적합하다.
```

주의:

```text
빠른 연속 요청 중 429 Too Many Requests가 발생했다.
따라서 sleep 1~2초, exponential backoff, 페이지별 raw 저장, checkpoint CSV가 필요하다.
```

## 1차 실행: 2025~2026 appid 실제 수집

명령:

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.search_release_window --start-year 2025 --end-year 2026 --stop-before-year 2025 --sleep-seconds 1.5
```

결과:

```text
pages_fetched=289
total_count=113,181
total_rows=28,899
unique_appids=28,899
start range=0~28,800
2026_trend=9,466
2025_trend_label_candidate=19,163
out_of_range=270
```

종료 조건:

```text
start=28,700과 start=28,800에서 2024년 페이지만 연속 확인
stop_reason=before_2025_for_2_pages
```

판단:

```text
2025~2026 출시 구간 appid 후보 전체 수집은 완료됐다.
다음 병목은 28,899개 전체 appdetails/review summary 수집이다.
이 단계는 장시간 실행될 수 있으므로 raw JSON 재사용, CSV checkpoint, 재실행 resume이 필요하다.
```

## 2차: 구버전 공식 app list 실패

시도한 URL:

```text
https://api.steampowered.com/ISteamApps/GetAppList/v2/?format=json
https://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json
```

결과:

```text
두 URL 모두 404
Method 'GetAppList' not found in interface 'ISteamApps'
```

판단:

```text
구버전 ISteamApps/GetAppList는 사용하지 않는다.
```

## 3차: 공식 IStoreService/GetAppList 확인

Steam Web API key를 `.env`에 넣은 뒤 공식 `IStoreService/GetAppList`를 확인했다.

```text
https://api.steampowered.com/IStoreService/GetAppList/v1/
status=200
max_results=10 정상 응답
```

비교:

```text
https://partner.steam-api.com/IStoreService/GetAppList/v1/
status=403
```

대량 수집 측정:

```text
공식 appid 50,000개: 약 3.8초
공식 appid 168,426개: 약 7.2~8.8초
max_appid=4,785,480
```

판단:

```text
공식 GetAppList는 game 후보 모집단 검증용으로 유용하다.
하지만 release date가 없으므로 2025~2026 게임을 직접 추출할 수 없다.
전체 16만 개를 모두 appdetails로 호출하는 것은 비효율적이다.
따라서 메인 수집이 아니라 상점 검색 결과의 누락/편향 검증에 사용한다.
```

## 4차: SteamSpy 확인

SteamSpy `request=all&page=N`을 확인했다.

```text
page당 약 1000개 appid 후보
10페이지 수집 결과: 10,000 rows, 9,960 unique
min_appid=10
max_appid=3,605,460
```

판단:

```text
SteamSpy는 빠르지만 공식 Steam 데이터가 아니다.
owners/인기권 중심 편향 가능성이 있으므로 메인 수집이 아니라 fallback과 인기권 누락 검증에 사용한다.
```

## 5차: 리뷰 timestamp 수집

2025년 후보 5개에 대해 Reviews API timestamp를 수집했다.

```text
review_timeline_rows=500
appids=5
소요 시간: 약 4.8초
각 appid당 100개 리뷰 수집 성공
```

판단:

```text
2025~2026 후보가 확보되면 리뷰 timestamp 수집은 정상 동작한다.
다음 병목은 리뷰 수집보다 Steam 상점 검색 구간 크롤링의 429 대응과 appdetails 호출량 관리다.
```

## 6차: SteamDB 검증 위치

SteamDB의 연도별 출시 통계는 외부 규모 검증 기준으로 사용한다.

```text
SteamDB는 자동 대량 크롤링 대상이 아니다.
보고서에서 Steam 상점 검색으로 확보한 2025 출시 규모가 외부 통계와 크게 어긋나는지 확인하는 기준으로 인용한다.
```

참고 링크:

```text
https://steamdb.info/stats/releases/
```

## 확정 결론

```text
메인:
Steam 상점 검색 Released_DESC로 2025~2026 출시 구간 수집

검증:
공식 IStoreService/GetAppList로 game 후보 모집단 차이 확인
SteamSpy로 인기권 게임 누락 여부 표본 확인
SteamDB로 연도별 출시 규모 외부 검증

fallback:
상점 검색이 막히면 공식 appid 표본 또는 SteamSpy appid 후보를 사용
```

## 예상 시간

```text
Steam 상점 검색 2025~2026 구간 appid 수집:
sleep 1~2초 기준 수십 분 단위 예상

appdetails:
후보 100개당 약 1~1.5분
28,899개 전체 기준 약 7~11시간 예상

review timeline:
게임 250개 x 500리뷰: 대략 30~60분 예상
게임 500개 x 500리뷰: 대략 60~120분 예상
```
