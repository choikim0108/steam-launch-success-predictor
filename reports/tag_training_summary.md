# Steam 태그별 학습 실행 요약

- 기준: 2025년까지 발매된 게임
- 요청: 태그별 75개 게임
- 처리 태그 수: 150
- 태그 배치: offset 0, limit 전체, resume True
- 요청 수량을 채운 태그 수: 150
- 모델 학습 게임 수: 2268
- 성공 라벨 게임 수: 633
- 성공 라벨 기준: 태그별 리뷰 수 상위 30% + 긍정률 75% 이상
- 표본 추출 방식: mixed
- 선택 모델: random_forest

상세 태그별 커버리지는 `reports/tag_training_coverage.csv`를 확인한다.
