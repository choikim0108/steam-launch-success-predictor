# 데이터 수집 1차~3차 시도 기록

## 목표

2025년 출시 Steam 게임을 기준으로 `success_90d`를 만들 수 있는 통합 데이터셋을 준비한다.

최종 데이터 흐름:

```text
appid 후보
-> appdetails
-> 2025년 출시 game 필터링
-> Reviews API timestamp 수집
-> 7/30/90일 리뷰 지표
-> success_90d
```

## 1차 시도: Steam 검색 기반 후보 수집

명령:

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.base --max-apps 50
```

결과:

```text
search_rows=50
detail_rows=50
review_summary_rows=50
소요 시간: 약 46초
```

판단:

```text
수집 자체는 정상 동작한다.
다만 최신 출시순 검색 결과는 현재 2026년 최신작부터 내려오기 때문에 2025년 학습 데이터 확보에는 비효율적이다.
검색 기반 수집은 빠른 smoke test와 직접 크롤링 source 확보용으로 사용한다.
```

## 2차 시도: API-first appid 후보 수집

시도한 공식 Steam app list URL:

```text
https://api.steampowered.com/ISteamApps/GetAppList/v2/?format=json
https://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json
```

결과:

```text
두 URL 모두 404
Method 'GetAppList' not found in interface 'ISteamApps'
```

대체 시도:

```text
https://steamspy.com/api.php?request=all&page=0
```

결과:

```text
status=200
page당 1000개 appid 후보
소요 시간: 약 0.4~0.7초/page
```

SteamSpy appid 후보 100개에 대해 appdetails를 수집해 2025년 게임을 필터링한 결과:

```text
sample_appids=100
소요 시간: 약 41~85초
2025년 출시 game=5개
```

판단:

```text
공식 GetAppList는 현재 환경에서 사용 불가.
API key가 있는 IStoreService/GetAppList를 확인하거나, SteamSpy all pagination을 후보 appid source로 사용한다.
SteamSpy는 appid 후보 확보에는 빠르지만 인기순/owners 중심 편향 가능성이 있으므로, 최종 보고서에서는 후보 source로 명시한다.
```

## 3차 시도: 2025년 후보 리뷰 타임라인 수집

2차에서 찾은 2025년 게임 5개에 대해 리뷰 timestamp를 수집했다.

대상 appid:

```text
2246340
1491000
3164500
1116170
3241660
```

명령:

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.review_timeline --input-csv steamspy_2025_sample.csv --max-reviews-per-game 100
```

결과:

```text
review_timeline_rows=500
appids=5
소요 시간: 약 4.8초
각 appid당 100개 리뷰 수집 성공
```

판단:

```text
2025년 후보가 확보되면 리뷰 timestamp 수집은 정상 동작한다.
다음 병목은 리뷰 수집이 아니라 2025년 후보 appid를 충분히 확보하는 단계다.
```

## End-to-end 샘플 측정

SteamSpy 1페이지 1000개 후보 중 appdetails 100개만 처리하고, 2025년 후보에 대해 게임당 리뷰 50개를 수집한 결과다.

명령 흐름:

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.steamspy_appids --pages 1
python -m steam_success.collect.appdetails_for_appids --max-apps 100
python -m steam_success.preprocess.candidate_filter --year 2025
python -m steam_success.collect.review_timeline --input-csv data/interim/game_candidates_2025.csv --max-reviews-per-game 50 --page-size 50
```

측정 결과:

```text
SteamSpy 후보 수집: 1.95초
appdetails + review summary 100개: 85.37초
2025년 후보 필터링: 1.09초
2025년 후보 수: 5개
리뷰 타임라인 5개 x 50리뷰: 6.05초
총 소요 시간: 94.47초
```

판단:

```text
실제 병목은 appdetails 수집이다.
후보 100개당 1~1.5분 정도로 잡는 것이 안전하다.
리뷰 타임라인은 후보 게임 수와 게임당 리뷰 제한을 낮게 잡으면 빠르게 검증 가능하다.
```

## 예상 시간

측정값 기준:

```text
SteamSpy 후보 100개 -> appdetails 필터링: 약 1~1.5분
SteamSpy 후보 1000개 -> appdetails 필터링: 약 10~15분
SteamSpy 후보 5000개 -> appdetails 필터링: 약 50~75분
SteamSpy 후보 10000개 -> appdetails 필터링: 약 100~150분
```

리뷰 타임라인:

```text
게임 5개 x 50~100리뷰: 약 5~6초
게임 250개 x 500리뷰: 대략 30~60분 예상
게임 500개 x 500리뷰: 대략 60~120분 예상
네트워크 제한이나 Steam 응답 지연이 있으면 더 늘어날 수 있음
```

## 일정에 넣을 수 있는 현실적 범위

MVP 실행:

```text
SteamSpy 후보 5000개
예상 2025년 후보 약 200~300개
게임당 리뷰 최대 500개
총 수집 예상 시간 약 2~3시간
```

확장 실행:

```text
SteamSpy 후보 10000개
예상 2025년 후보 약 400~600개
게임당 리뷰 최대 500~1000개
총 수집 예상 시간 약 4~6시간
```

팀 일정상 권장:

```text
먼저 5000개 후보로 MVP 데이터셋을 확정한다.
EDA와 모델링이 돌아가는 것을 확인한 뒤, 시간이 남으면 10000개 후보로 확장한다.
처음부터 10000개 이상을 목표로 잡으면 전처리와 검증 시간이 부족해질 수 있다.
```

## 확정 계획

```text
1차:
검색 기반 수집 50~300개로 파이프라인 smoke test

2차:
SteamSpy pages 5~10개에서 appid 5000~10000개 확보
appdetails로 2025년 출시 game 필터링

3차:
필터링된 2025년 후보에 Reviews API timeline 수집
max_reviews_per_game=500부터 시작
```

## 안 되는 것 / 주의할 것

```text
공식 ISteamApps/GetAppList는 현재 환경에서 404로 실패.
검색 기반 최신순 수집은 2025년 학습 데이터 확보에는 비효율적.
SteamSpy all은 빠르지만 전체 Steam 모집단의 무편향 목록이라고 단정하면 안 됨.
최종적으로 API key가 확보되면 IStoreService/GetAppList를 다시 검토한다.
```
