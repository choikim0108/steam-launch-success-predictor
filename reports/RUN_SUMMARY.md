# Steam 출시 성공 예측 모델 실행 결과

- 모델링 데이터 수: 39
- 성공 라벨 수: 14
- 비성공 라벨 수: 25
- 선택 모델: random_forest
- 테스트 Accuracy: 1.000
- 테스트 Precision: 1.000
- 테스트 Recall: 1.000
- 테스트 F1: 1.000

## 주요 피처 중요도
- youtube_mentions: 0.2601
- external_attention_score: 0.2030
- price_final_usd: 0.1217
- category_count: 0.1106
- supported_language_count: 0.0924
- discount_percent: 0.0860
- genre_count: 0.0381
- has_multiplayer: 0.0219

## 장르별 결론 상위 항목
- Sports: 성공 2개 / 전체 3개, 성공률 66.7%
- Early Access: 성공 6개 / 전체 13개, 성공률 46.2%
- RPG: 성공 4개 / 전체 9개, 성공률 44.4%
- Adventure: 성공 7개 / 전체 16개, 성공률 43.8%
- Simulation: 성공 6개 / 전체 16개, 성공률 37.5%
- Action: 성공 7개 / 전체 19개, 성공률 36.8%
- Strategy: 성공 3개 / 전체 9개, 성공률 33.3%
- Indie: 성공 8개 / 전체 26개, 성공률 30.8%

## 생성 차트
- `reports/figures/label_distribution.png`
- `reports/figures/reviews_vs_positive_rate.png`
- `reports/figures/feature_importance.png`

## 결론 위치
- 상세 결론과 해석 주의사항은 `reports/CONCLUSIONS.md`에 저장했다.

## 해석 주의
- 이 결과는 Steam `popularnew` 검색 노출 샘플 기반이므로 전체 Steam 시장의 무작위 표본은 아니다. 성공/실패 비율은 모델 학습용 라벨 분포이지 실제 시장 성공률로 해석하면 안 된다.
