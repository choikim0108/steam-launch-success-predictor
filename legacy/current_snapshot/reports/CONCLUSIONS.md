# 실제 결론 및 해석

## 핵심 결론
이번 수집 데이터에서는 성공 라벨이 133개, 비성공 라벨이 46개이며 성공 라벨 비율은 74.3%이다. 이 비율은 Steam 전체 시장 성공률이 아니라 `popularnew` 검색 결과에서 수집된 표본과 현재 성공 기준에 따른 학습용 라벨 분포다.

## 그래서 성공할 것으로 예측되는 게임은 뭔가?
현재 모델이 가장 성공 가능성이 높다고 예측한 게임은 [Manor Lords](https://store.steampowered.com/app/1363080/)이다. 예측 성공 확률은 90.3%이며, 현재 수집 기준에서는 리뷰 87,243개와 긍정률 84.4%로 성공 기준을 충족.

## 성공 게임이 많이 나타난 장르
- Casual: 성공 29개 / 전체 36개, 성공률 80.6%
- Adventure: 성공 72개 / 전체 91개, 성공률 79.1%
- Indie: 성공 65개 / 전체 83개, 성공률 78.3%
- Action: 성공 77개 / 전체 101개, 성공률 76.2%
- Early Access: 성공 29개 / 전체 39개, 성공률 74.4%
- Simulation: 성공 53개 / 전체 72개, 성공률 73.6%
- RPG: 성공 44개 / 전체 62개, 성공률 71.0%
- Strategy: 성공 29개 / 전체 41개, 성공률 70.7%
- Sports: 성공 8개 / 전체 12개, 성공률 66.7%
- Racing: 성공 5개 / 전체 8개, 성공률 62.5%

## 다양한 기준별 결과
### 상점 기능/카테고리
- Remote Play on TV: 성공 9개 / 전체 9개, 성공률 100.0%
- Touch Only Option: 성공 6개 / 전체 6개, 성공률 100.0%
- Shared/Split Screen: 성공 12개 / 전체 14개, 성공률 85.7%
- Full controller support: 성공 91개 / 전체 109개, 성공률 83.5%
- Remote Play Together: 성공 10개 / 전체 12개, 성공률 83.3%

### 가격대
- 60_plus: 성공 6개 / 전체 7개, 성공률 85.7%
- 10_to_30: 성공 63개 / 전체 81개, 성공률 77.8%
- under_10: 성공 27개 / 전체 35개, 성공률 77.1%
- 30_to_60: 성공 29개 / 전체 42개, 성공률 69.0%
- free: 성공 8개 / 전체 14개, 성공률 57.1%

### 지원 언어 수
- 31_plus: 성공 1개 / 전체 1개, 성공률 100.0%
- 16_30: 성공 35개 / 전체 40개, 성공률 87.5%
- 1_5: 성공 15개 / 전체 21개, 성공률 71.4%
- 6_15: 성공 82개 / 전체 117개, 성공률 70.1%

### 지원 플랫폼 수
- 3 platforms: 성공 6개 / 전체 7개, 성공률 85.7%
- 2 platforms: 성공 21개 / 전체 26개, 성공률 80.8%
- 1 platforms: 성공 106개 / 전체 146개, 성공률 72.6%

### 멀티플레이 여부
- no: 성공 64개 / 전체 81개, 성공률 79.0%
- yes: 성공 69개 / 전체 98개, 성공률 70.4%

### 외부 웹 관심도
- high: 성공 9개 / 전체 9개, 성공률 100.0%
- medium: 성공 3개 / 전체 3개, 성공률 100.0%
- none: 성공 121개 / 전체 167개, 성공률 72.5%

## 성공확률 상위 장르의 성공/실패 게임 리뷰 토픽
- Casual / success 게임 / positive 리뷰: que, game, se, 10, en, jogo, um, el (리뷰 71개)
- Casual / success 게임 / negative 리뷰: game, la, le, des, good, les, play, sur (리뷰 9개)
- Casual / failure 게임 / positive 리뷰: game, like, love, die, great, just, good, ist (리뷰 61개)
- Casual / failure 게임 / negative 리뷰: game, just, little, machines, really, experience, ich, like (리뷰 19개)
- Indie / success 게임 / positive 리뷰: game, que, fun, good, jogo, se, es, 10 (리뷰 241개)
- Indie / success 게임 / negative 리뷰: game, good, le, la, boring, fun, jest, like (리뷰 39개)
- Indie / failure 게임 / positive 리뷰: game, le, just, like, love, great, en, et (리뷰 83개)
- Indie / failure 게임 / negative 리뷰: game, la, est, et, jeu, pour, que, en (리뷰 37개)
- Simulation / success 게임 / positive 리뷰: game, que, en, es, fun, el, se, al (리뷰 104개)
- Simulation / success 게임 / negative 리뷰: game, le, la, des, avoir, boring, sur, tout (리뷰 16개)
- Simulation / failure 게임 / positive 리뷰: game, like, love, fun, good, great, just, que (리뷰 124개)
- Simulation / failure 게임 / negative 리뷰: game, est, et, jeu, just, pour, la, les (리뷰 36개)

## 게임 서비스 개선 및 시장 분석 결론
시장 분석에서는 성공확률 상위 장르의 긍정 키워드(Casual: que, game, se, 10, en, jogo, um, el; Indie: game, que, fun, good, jogo, se, es, 10; Simulation: game, que, en, es, fun, el, se, al)를 신작 포지셔닝 메시지와 Steam 태그 전략에 반영하는 것이 우선이다. 서비스 개선에서는 성공/실패 게임의 부정 키워드(Indie: game, good, le, la, boring, fun, jest, like; Indie: game, la, est, et, jeu, pour, que, en; Simulation: game, est, et, jeu, just, pour, la, les)를 출시 직후 패치, 튜토리얼, 밸런스, 콘텐츠 보강 우선순위로 관리해야 한다.

## 모델 결과 해석
- 선택 모델 기준 테스트 Accuracy는 0.722, F1은 0.819이다.
- F1은 성공/실패 양쪽을 함께 보는 지표라 Accuracy만 보는 것보다 현재 분류 문제에 더 적합하다.
- 현재처럼 성공 133개/비성공 46개로 한쪽이 더 많은 분포는 학습 자체를 막을 수준은 아니지만, 전체 표본 수와 수집 편향 때문에 장르별 결론이 흔들릴 수 있다.

## 유의미성 판단
현재 결과는 '실행 가능한 탐색 모델'로는 유의미하지만, 최종 일반화 결론으로 보기에는 제한이 있다. 이유는 표본이 Steam 전체 무작위 표본이 아니고, 성공 기준이 실제 매출이 아닌 리뷰 수와 긍정률 proxy이기 때문이다. 따라서 보고서에서는 '현재 수집 표본에서는 이런 경향이 보였다'고 표현하는 것이 안전하다.

## 추가 개선 방향
- `src/steam_success/config.py`에서 `max_apps`를 더 늘려 재수집한다.
- 장르별 최소 표본 수를 10개 이상으로 높인 뒤 장르 결론을 다시 해석한다.
- 리뷰 500개/긍정률 80% 기준과 장르별 상위 분위수 기준을 함께 비교한다.
