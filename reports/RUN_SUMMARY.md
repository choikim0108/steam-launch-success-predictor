# Steam 출시 성공 예측 모델 실행 결과

- 모델링 데이터 수: 2268
- 성공 라벨 수: 633
- 비성공 라벨 수: 1635
- 선택 모델: random_forest
- 테스트 Accuracy: 0.708
- 테스트 Precision: 0.484
- 테스트 Recall: 0.711
- 테스트 F1: 0.576

## 주요 피처 중요도
- price_final_usd: 0.2300
- supported_language_count: 0.1920
- category_count: 0.1227
- supports_controller: 0.1099
- supports_achievements: 0.0818
- genre_count: 0.0718
- platform_mac: 0.0417
- platform_linux: 0.0414

## 그래서 성공할 것으로 예측되는 게임
- [Dying Light](https://store.steampowered.com/app/239140/)
- 예측 성공 확률: 89.1%
- 현재 성공 기준 충족 여부: 충족
- 리뷰 수/긍정률: 487,803개 / 95.2%

## 성공확률 상위 장르 리뷰 토픽 분석
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

## 서비스 개선 및 시장 분석 결론
시장 분석에서는 성공확률 상위 장르의 긍정 키워드(Massively Multiplayer: combat, servers, gameplay, grind, maps; Action: gameplay, story, content, combat, grind; Adventure: story, gameplay, content, servers, combat, grind)를 신작 포지셔닝 메시지와 Steam 태그 전략에 반영하는 것이 우선이다. 서비스 개선에서는 성공/실패 게임의 부정 키워드(Action: gameplay, servers, matchmaking, bugs, content; Action: level, story, combat; Adventure: story, level, combat)를 출시 직후 패치, 튜토리얼, 밸런스, 콘텐츠 보강 우선순위로 관리해야 한다.

## 장르별 결론 상위 항목
- Free To Play: 성공 201개 / 전체 616개, 성공률 32.6%
- Adventure: 성공 276개 / 전체 987개, 성공률 28.0%
- Indie: 성공 369개 / 전체 1329개, 성공률 27.8%
- Action: 성공 271개 / 전체 1037개, 성공률 26.1%
- RPG: 성공 164개 / 전체 677개, 성공률 24.2%
- Massively Multiplayer: 성공 47개 / 전체 210개, 성공률 22.4%
- Casual: 성공 208개 / 전체 953개, 성공률 21.8%
- Simulation: 성공 143개 / 전체 667개, 성공률 21.4%

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
