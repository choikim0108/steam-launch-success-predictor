# Steam 출시 성공 예측 모델 실행 결과

- 모델링 데이터 수: 22473
- 성공 라벨 수: 636
- 비성공 라벨 수: 21837
- 선택 모델: random_forest
- 테스트 Accuracy: 0.827
- 테스트 Precision: 0.103
- 테스트 Recall: 0.660
- 테스트 F1: 0.178

## 주요 피처 중요도
- price_final_usd: 0.2854
- supported_language_count: 0.2813
- supports_achievements: 0.1406
- category_count: 0.1182
- supports_controller: 0.0436
- discount_percent: 0.0411
- genre_count: 0.0268
- platform_mac: 0.0257

## 그래서 성공할 것으로 예측되는 게임
- [Clair Obscur: Expedition 33](https://store.steampowered.com/app/1903340/)
- 예측 성공 확률: 90.8%
- 현재 성공 기준 충족 여부: 충족
- 리뷰 수/긍정률: 98,475개 / 95.4%

## 성공확률 상위 장르 리뷰 토픽 분석
- 리뷰 토픽 분석 결과가 아직 생성되지 않았다.

## 서비스 개선 및 시장 분석 결론
리뷰 토픽 분석 결과가 부족해 서비스 개선과 시장 분석 결론을 만들 수 없다.

## 장르별 결론 상위 항목
- RPG: 성공 215개 / 전체 4253개, 성공률 5.1% (n=4253)
- Simulation: 성공 241개 / 전체 5262개, 성공률 4.6% (n=5262)
- Early Access: 성공 100개 / 전체 2607개, 성공률 3.8% (n=2607)
- Adventure: 성공 295개 / 전체 8836개, 성공률 3.3% (n=8836)
- Strategy: 성공 157개 / 전체 4922개, 성공률 3.2% (n=4922)
- Action: 성공 248개 / 전체 8741개, 성공률 2.8% (n=8741)
- Indie: 성공 415개 / 전체 16277개, 성공률 2.5% (n=16277)
- Casual: 성공 225개 / 전체 10257개, 성공률 2.2% (n=10257)

## 생성 차트
- `90d/figures/label_distribution.png`
- `90d/figures/reviews_vs_positive_rate.png`
- `90d/figures/feature_importance.png`
- `90d/figures/analysis_workflow.png`

## 결론 위치
- 상세 결론과 해석 주의사항은 `reports/CONCLUSIONS.md`에 저장했다.

## 해석 주의
- 이 결과는 Steam `popularnew` 검색 노출 샘플 기반이므로 전체 Steam 시장의 무작위 표본은 아니다. 성공/실패 비율은 모델 학습용 라벨 분포이지 실제 시장 성공률로 해석하면 안 된다.
