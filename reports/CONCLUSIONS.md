# 실제 결론 및 해석

## 핵심 결론
이번 수집 데이터에서는 성공 라벨이 633개, 비성공 라벨이 1635개이며 성공 라벨 비율은 27.9%이다. 이 비율은 Steam 전체 시장 성공률이 아니라 `popularnew` 검색 결과에서 수집된 표본과 현재 성공 기준에 따른 학습용 라벨 분포다.

## 그래서 성공할 것으로 예측되는 게임은 뭔가?
현재 모델이 가장 성공 가능성이 높다고 예측한 게임은 [Dying Light](https://store.steampowered.com/app/239140/)이다. 예측 성공 확률은 89.1%이며, 현재 수집 기준에서는 리뷰 487,803개와 긍정률 95.2%로 성공 기준을 충족.

## 성공 게임이 많이 나타난 장르
- Free To Play: 성공 201개 / 전체 616개, 성공률 32.6%
- Adventure: 성공 276개 / 전체 987개, 성공률 28.0%
- Indie: 성공 369개 / 전체 1329개, 성공률 27.8%
- Action: 성공 271개 / 전체 1037개, 성공률 26.1%
- RPG: 성공 164개 / 전체 677개, 성공률 24.2%
- Massively Multiplayer: 성공 47개 / 전체 210개, 성공률 22.4%
- Casual: 성공 208개 / 전체 953개, 성공률 21.8%
- Simulation: 성공 143개 / 전체 667개, 성공률 21.4%
- Strategy: 성공 120개 / 전체 563개, 성공률 21.3%
- Early Access: 성공 35개 / 전체 177개, 성공률 19.8%

## 다양한 기준별 결과
### 상점 기능/카테고리
- Includes Source SDK: 성공 6개 / 전체 6개, 성공률 100.0%
- Remote Play on Tablet: 성공 91개 / 전체 115개, 성공률 79.1%
- Remote Play on Phone: 성공 67개 / 전체 86개, 성공률 77.9%
- Valve Anti-Cheat enabled: 성공 15개 / 전체 20개, 성공률 75.0%
- Remote Play on TV: 성공 72개 / 전체 102개, 성공률 70.6%

### 가격대
- 10_to_30: 성공 154개 / 전체 334개, 성공률 46.1%
- free: 성공 236개 / 전체 697개, 성공률 33.9%
- 30_to_60: 성공 86개 / 전체 262개, 성공률 32.8%
- under_10: 성공 145개 / 전체 634개, 성공률 22.9%
- 60_plus: 성공 12개 / 전체 341개, 성공률 3.5%

### 지원 언어 수
- 6_15: 성공 276개 / 전체 665개, 성공률 41.5%
- 16_30: 성공 102개 / 전체 262개, 성공률 38.9%
- 1_5: 성공 249개 / 전체 1158개, 성공률 21.5%
- 31_plus: 성공 6개 / 전체 183개, 성공률 3.3%

### 지원 플랫폼 수
- 2 platforms: 성공 138개 / 전체 310개, 성공률 44.5%
- 3 platforms: 성공 123개 / 전체 429개, 성공률 28.7%
- 1 platforms: 성공 372개 / 전체 1529개, 성공률 24.3%

### 멀티플레이 여부
- yes: 성공 222개 / 전체 693개, 성공률 32.0%
- no: 성공 411개 / 전체 1575개, 성공률 26.1%

### 외부 웹 관심도
- medium: 성공 10개 / 전체 10개, 성공률 100.0%
- high: 성공 2개 / 전체 2개, 성공률 100.0%
- none: 성공 621개 / 전체 2256개, 성공률 27.5%

## 성공확률 상위 장르의 성공/실패 게임 리뷰 토픽
- Massively Multiplayer / success 게임 / positive 리뷰: combat, servers, gameplay, grind, maps (리뷰 402개)
- Massively Multiplayer / success 게임 / negative 리뷰: servers, bugs, matchmaking, performance, content (리뷰 195개)
- Massively Multiplayer / failure 게임 / positive 리뷰: gameplay, combat, content, quests, maps (리뷰 386개)
- Massively Multiplayer / failure 게임 / negative 리뷰: grind, level, story, content, combat, gameplay (리뷰 212개)
- Action / success 게임 / positive 리뷰: gameplay, story, content, combat, grind (리뷰 2259개)
- Action / success 게임 / negative 리뷰: gameplay, servers, matchmaking, bugs, content (리뷰 429개)
- Action / failure 게임 / positive 리뷰: gameplay, combat, maps, story, weapon (리뷰 695개)
- Action / failure 게임 / negative 리뷰: level, story, combat (리뷰 403개)
- Adventure / success 게임 / positive 리뷰: story, gameplay, content, servers, combat, grind (리뷰 1100개)
- Adventure / success 게임 / negative 리뷰: progression, gameplay, servers, bugs, content (리뷰 197개)
- Adventure / failure 게임 / positive 리뷰: gameplay, combat, story, performance, weapon, content, maps (리뷰 450개)
- Adventure / failure 게임 / negative 리뷰: story, level, combat (리뷰 248개)

## 게임 서비스 개선 및 시장 분석 결론
시장 분석에서는 성공확률 상위 장르의 긍정 키워드(Massively Multiplayer: combat, servers, gameplay, grind, maps; Action: gameplay, story, content, combat, grind; Adventure: story, gameplay, content, servers, combat, grind)를 신작 포지셔닝 메시지와 Steam 태그 전략에 반영하는 것이 우선이다. 서비스 개선에서는 성공/실패 게임의 부정 키워드(Action: gameplay, servers, matchmaking, bugs, content; Action: level, story, combat; Adventure: story, level, combat)를 출시 직후 패치, 튜토리얼, 밸런스, 콘텐츠 보강 우선순위로 관리해야 한다.

## 모델 결과 해석
- 선택 모델 기준 테스트 Accuracy는 0.708, F1은 0.576이다.
- F1은 성공/실패 양쪽을 함께 보는 지표라 Accuracy만 보는 것보다 현재 분류 문제에 더 적합하다.
- 현재처럼 성공 633개/비성공 1635개로 한쪽이 더 많은 분포는 학습 자체를 막을 수준은 아니지만, 전체 표본 수와 수집 편향 때문에 장르별 결론이 흔들릴 수 있다.

## 유의미성 판단
현재 결과는 '실행 가능한 탐색 모델'로는 유의미하지만, 최종 일반화 결론으로 보기에는 제한이 있다. 이유는 표본이 Steam 전체 무작위 표본이 아니고, 성공 기준이 실제 매출이 아닌 리뷰 수와 긍정률 proxy이기 때문이다. 따라서 보고서에서는 '현재 수집 표본에서는 이런 경향이 보였다'고 표현하는 것이 안전하다.

## 추가 개선 방향
- `src/steam_success/config.py`에서 `max_apps`를 더 늘려 재수집한다.
- 장르별 최소 표본 수를 10개 이상으로 높인 뒤 장르 결론을 다시 해석한다.
- 리뷰 500개/긍정률 80% 기준과 장르별 상위 분위수 기준을 함께 비교한다.
