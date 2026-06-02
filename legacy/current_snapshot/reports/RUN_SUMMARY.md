# Steam 출시 성공 예측 모델 실행 결과

- 모델링 데이터 수: 179
- 성공 라벨 수: 133
- 비성공 라벨 수: 46
- 선택 모델: random_forest
- 테스트 Accuracy: 0.722
- 테스트 Precision: 0.791
- 테스트 Recall: 0.850
- 테스트 F1: 0.819

## 주요 피처 중요도
- supported_language_count: 0.1798
- genre_count: 0.1693
- price_final_usd: 0.1610
- category_count: 0.1540
- discount_percent: 0.1136
- has_multiplayer: 0.0547
- has_singleplayer: 0.0373
- required_age: 0.0254

## 그래서 성공할 것으로 예측되는 게임
- [Manor Lords](https://store.steampowered.com/app/1363080/)
- 예측 성공 확률: 90.3%
- 현재 성공 기준 충족 여부: 충족
- 리뷰 수/긍정률: 87,243개 / 84.4%

## 성공확률 상위 장르 리뷰 토픽 분석
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

## 서비스 개선 및 시장 분석 결론
시장 분석에서는 성공확률 상위 장르의 긍정 키워드(Casual: que, game, se, 10, en, jogo, um, el; Indie: game, que, fun, good, jogo, se, es, 10; Simulation: game, que, en, es, fun, el, se, al)를 신작 포지셔닝 메시지와 Steam 태그 전략에 반영하는 것이 우선이다. 서비스 개선에서는 성공/실패 게임의 부정 키워드(Indie: game, good, le, la, boring, fun, jest, like; Indie: game, la, est, et, jeu, pour, que, en; Simulation: game, est, et, jeu, just, pour, la, les)를 출시 직후 패치, 튜토리얼, 밸런스, 콘텐츠 보강 우선순위로 관리해야 한다.

## 장르별 결론 상위 항목
- Casual: 성공 29개 / 전체 36개, 성공률 80.6%
- Adventure: 성공 72개 / 전체 91개, 성공률 79.1%
- Indie: 성공 65개 / 전체 83개, 성공률 78.3%
- Action: 성공 77개 / 전체 101개, 성공률 76.2%
- Early Access: 성공 29개 / 전체 39개, 성공률 74.4%
- Simulation: 성공 53개 / 전체 72개, 성공률 73.6%
- RPG: 성공 44개 / 전체 62개, 성공률 71.0%
- Strategy: 성공 29개 / 전체 41개, 성공률 70.7%

## 생성 차트
- `reports/figures/label_distribution.png`
- `reports/figures/reviews_vs_positive_rate.png`
- `reports/figures/feature_importance.png`
- `reports/figures/analysis_workflow.png`
- `reports/figures/review_topic_counts.png`

## 결론 위치
- 상세 결론과 해석 주의사항은 `reports/CONCLUSIONS.md`에 저장했다.

## 해석 주의
- 이 결과는 Steam `popularnew` 검색 노출 샘플 기반이므로 전체 Steam 시장의 무작위 표본은 아니다. 성공/실패 비율은 모델 학습용 라벨 분포이지 실제 시장 성공률로 해석하면 안 된다.
