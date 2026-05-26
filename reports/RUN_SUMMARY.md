# Steam 출시 성공 예측 모델 실행 결과

- 모델링 데이터 수: 111
- 성공 라벨 수: 68
- 비성공 라벨 수: 43
- 선택 모델: random_forest
- 테스트 Accuracy: 0.559
- 테스트 Precision: 0.607
- 테스트 Recall: 0.810
- 테스트 F1: 0.694

## 주요 피처 중요도
- price_final_usd: 0.1915
- discount_percent: 0.1782
- category_count: 0.1551
- supported_language_count: 0.1270
- metacritic_score: 0.0961
- genre_count: 0.0772
- has_singleplayer: 0.0268
- supports_controller: 0.0260

## 장르별 결론 상위 항목
- RPG: 성공 23개 / 전체 33개, 성공률 69.7%
- Adventure: 성공 38개 / 전체 55개, 성공률 69.1%
- Racing: 성공 2개 / 전체 3개, 성공률 66.7%
- Sports: 성공 2개 / 전체 3개, 성공률 66.7%
- Action: 성공 48개 / 전체 73개, 성공률 65.8%
- Strategy: 성공 19개 / 전체 30개, 성공률 63.3%
- Early Access: 성공 18개 / 전체 31개, 성공률 58.1%
- Indie: 성공 27개 / 전체 48개, 성공률 56.2%

## 생성 차트
- `reports/figures/label_distribution.png`
- `reports/figures/reviews_vs_positive_rate.png`
- `reports/figures/feature_importance.png`

## 결론 위치
- 상세 결론과 해석 주의사항은 `reports/CONCLUSIONS.md`에 저장했다.

## 해석 주의
- 이 결과는 Steam `popularnew` 검색 노출 샘플 기반이므로 전체 Steam 시장의 무작위 표본은 아니다. 성공/실패 비율은 모델 학습용 라벨 분포이지 실제 시장 성공률로 해석하면 안 된다.
