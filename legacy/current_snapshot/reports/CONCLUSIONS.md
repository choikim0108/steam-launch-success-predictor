# 실제 결론 및 해석

## 핵심 결론
이번 수집 데이터에서는 성공 라벨이 123개, 비성공 라벨이 55개이며 성공 라벨 비율은 69.1%이다. 이 비율은 Steam 전체 시장 성공률이 아니라 `popularnew` 검색 결과에서 수집된 표본과 현재 성공 기준에 따른 학습용 라벨 분포다.

## 그래서 성공할 것으로 예측되는 게임은 뭔가?
현재 모델이 가장 성공 가능성이 높다고 예측한 게임은 [Clair Obscur: Expedition 33](https://store.steampowered.com/app/1903340/)이다. 예측 성공 확률은 93.7%이며, 현재 수집 기준에서는 리뷰 267,144개와 긍정률 95.4%로 성공 기준을 충족.

## 성공 게임이 많이 나타난 장르
- Casual: 성공 22개 / 전체 29개, 성공률 75.9%
- Simulation: 성공 47개 / 전체 65개, 성공률 72.3%
- Adventure: 성공 58개 / 전체 82개, 성공률 70.7%
- Strategy: 성공 33개 / 전체 47개, 성공률 70.2%
- Early Access: 성공 31개 / 전체 45개, 성공률 68.9%
- RPG: 성공 44개 / 전체 64개, 성공률 68.8%
- Action: 성공 70개 / 전체 102개, 성공률 68.6%
- Indie: 성공 54개 / 전체 80개, 성공률 67.5%
- Sports: 성공 6개 / 전체 9개, 성공률 66.7%
- Racing: 성공 3개 / 전체 5개, 성공률 60.0%

## 다양한 기준별 결과
### 상점 기능/카테고리
- Includes level editor: 성공 6개 / 전체 6개, 성공률 100.0%
- LAN PvP: 성공 3개 / 전체 3개, 성공률 100.0%
- Remote Play on TV: 성공 8개 / 전체 9개, 성공률 88.9%
- LAN Co-op: 성공 5개 / 전체 6개, 성공률 83.3%
- Remote Play on Tablet: 성공 5개 / 전체 6개, 성공률 83.3%

### 가격대
- 60_plus: 성공 8개 / 전체 9개, 성공률 88.9%
- under_10: 성공 25개 / 전체 33개, 성공률 75.8%
- 10_to_30: 성공 58개 / 전체 84개, 성공률 69.0%
- 30_to_60: 성공 27개 / 전체 40개, 성공률 67.5%
- free: 성공 5개 / 전체 12개, 성공률 41.7%

### 지원 언어 수
- 16_30: 성공 36개 / 전체 43개, 성공률 83.7%
- 1_5: 성공 15개 / 전체 21개, 성공률 71.4%
- 6_15: 성공 72개 / 전체 114개, 성공률 63.2%

### 지원 플랫폼 수
- 2 platforms: 성공 23개 / 전체 31개, 성공률 74.2%
- 1 platforms: 성공 96개 / 전체 141개, 성공률 68.1%
- 3 platforms: 성공 4개 / 전체 6개, 성공률 66.7%

### 멀티플레이 여부
- no: 성공 62개 / 전체 83개, 성공률 74.7%
- yes: 성공 61개 / 전체 95개, 성공률 64.2%

### 외부 웹 관심도
- high: 성공 10개 / 전체 10개, 성공률 100.0%
- medium: 성공 2개 / 전체 2개, 성공률 100.0%
- none: 성공 111개 / 전체 166개, 성공률 66.9%

## 성공확률 상위 장르의 성공/실패 게임 리뷰 토픽
- Adventure / success 게임 / positive 리뷰: game, ayy, ayy ayy, les, que, ella, et, 10 (리뷰 180개)
- Adventure / success 게임 / negative 리뷰: es, nie, ale, eine, game, ist, kt, na (리뷰 18개)
- Adventure / failure 게임 / positive 리뷰: game, good, better, great, like, love, play, games (리뷰 75개)
- Adventure / failure 게임 / negative 리뷰: game, para, um, ncia, que, em, jogo, experi (리뷰 25개)
- Action / success 게임 / positive 리뷰: game, ayy, ayy ayy, les, que, like, 10, ella (리뷰 261개)
- Action / success 게임 / negative 리뷰: game, pve, just, pvp, like, player, ai, time (리뷰 36개)
- Action / failure 게임 / positive 리뷰: game, good, like, better, di, il, love, played (리뷰 98개)
- Action / failure 게임 / negative 리뷰: game, para, um, really, ncia, que, good, play (리뷰 42개)
- Strategy / success 게임 / positive 리뷰: game, factory, like, fun, 10, factory grow, grow, good (리뷰 73개)
- Strategy / success 게임 / negative 리뷰: nie, ale, game, kt, na, pause, si, art (리뷰 6개)
- Strategy / failure 게임 / positive 리뷰: game, di, il, good, great, love, non, play (리뷰 61개)
- Strategy / failure 게임 / negative 리뷰: game, para, um, ncia, que, really, em, jogo (리뷰 19개)

## 게임 서비스 개선 및 시장 분석 결론
시장 분석에서는 성공확률 상위 장르의 긍정 키워드(Adventure: game, ayy, ayy ayy, les, que, ella, et, 10; Action: game, ayy, ayy ayy, les, que, like, 10, ella; Strategy: game, factory, like, fun, 10, factory grow, grow, good)를 신작 포지셔닝 메시지와 Steam 태그 전략에 반영하는 것이 우선이다. 서비스 개선에서는 성공/실패 게임의 부정 키워드(Action: game, para, um, really, ncia, que, good, play; Action: game, pve, just, pvp, like, player, ai, time; Adventure: game, para, um, ncia, que, em, jogo, experi)를 출시 직후 패치, 튜토리얼, 밸런스, 콘텐츠 보강 우선순위로 관리해야 한다.

## 모델 결과 해석
- 선택 모델 기준 테스트 Accuracy는 0.685, F1은 0.767이다.
- F1은 성공/실패 양쪽을 함께 보는 지표라 Accuracy만 보는 것보다 현재 분류 문제에 더 적합하다.
- 현재처럼 성공 123개/비성공 55개로 한쪽이 더 많은 분포는 학습 자체를 막을 수준은 아니지만, 전체 표본 수와 수집 편향 때문에 장르별 결론이 흔들릴 수 있다.

## 유의미성 판단
현재 결과는 '실행 가능한 탐색 모델'로는 유의미하지만, 최종 일반화 결론으로 보기에는 제한이 있다. 이유는 표본이 Steam 전체 무작위 표본이 아니고, 성공 기준이 실제 매출이 아닌 리뷰 수와 긍정률 proxy이기 때문이다. 따라서 보고서에서는 '현재 수집 표본에서는 이런 경향이 보였다'고 표현하는 것이 안전하다.

## 추가 개선 방향
- `src/steam_success/config.py`에서 `max_apps`를 더 늘려 재수집한다.
- 장르별 최소 표본 수를 10개 이상으로 높인 뒤 장르 결론을 다시 해석한다.
- 리뷰 500개/긍정률 80% 기준과 장르별 상위 분위수 기준을 함께 비교한다.
