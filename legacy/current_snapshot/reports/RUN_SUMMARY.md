# Steam 출시 성공 예측 모델 실행 결과

- 모델링 데이터 수: 178
- 성공 라벨 수: 123
- 비성공 라벨 수: 55
- 선택 모델: random_forest
- 테스트 Accuracy: 0.685
- 테스트 Precision: 0.778
- 테스트 Recall: 0.757
- 테스트 F1: 0.767

## 주요 피처 중요도
- supported_language_count: 0.2237
- price_final_usd: 0.1574
- category_count: 0.1356
- discount_percent: 0.1180
- metacritic_score: 0.0849
- genre_count: 0.0833
- has_multiplayer: 0.0373
- supports_achievements: 0.0273

## 그래서 성공할 것으로 예측되는 게임
- [Clair Obscur: Expedition 33](https://store.steampowered.com/app/1903340/)
- 예측 성공 확률: 93.7%
- 현재 성공 기준 충족 여부: 충족
- 리뷰 수/긍정률: 267,144개 / 95.4%

## 성공확률 상위 장르 리뷰 토픽 분석
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

## 서비스 개선 및 시장 분석 결론
시장 분석에서는 성공확률 상위 장르의 긍정 키워드(Adventure: game, ayy, ayy ayy, les, que, ella, et, 10; Action: game, ayy, ayy ayy, les, que, like, 10, ella; Strategy: game, factory, like, fun, 10, factory grow, grow, good)를 신작 포지셔닝 메시지와 Steam 태그 전략에 반영하는 것이 우선이다. 서비스 개선에서는 성공/실패 게임의 부정 키워드(Action: game, para, um, really, ncia, que, good, play; Action: game, pve, just, pvp, like, player, ai, time; Adventure: game, para, um, ncia, que, em, jogo, experi)를 출시 직후 패치, 튜토리얼, 밸런스, 콘텐츠 보강 우선순위로 관리해야 한다.

## 장르별 결론 상위 항목
- Casual: 성공 22개 / 전체 29개, 성공률 75.9%
- Simulation: 성공 47개 / 전체 65개, 성공률 72.3%
- Adventure: 성공 58개 / 전체 82개, 성공률 70.7%
- Strategy: 성공 33개 / 전체 47개, 성공률 70.2%
- Early Access: 성공 31개 / 전체 45개, 성공률 68.9%
- RPG: 성공 44개 / 전체 64개, 성공률 68.8%
- Action: 성공 70개 / 전체 102개, 성공률 68.6%
- Indie: 성공 54개 / 전체 80개, 성공률 67.5%

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
