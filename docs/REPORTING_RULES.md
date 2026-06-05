# 리포트 해석 상수 기준

이 문서는 생성 리포트에 남는 도메인 상수의 의도를 설명한다.

## 성공/중박/실패 표시 기준

- `ProjectSettings.outcome_success_probability_threshold`: 정적 리포트에서 예측 확률이 성공권으로 보이는 기준이다. 현재 값은 `0.65`이다.
- `ProjectSettings.outcome_mid_probability_threshold`: 중박권과 실패권을 나누는 표시 기준이다. 현재 값은 `0.35`이다.
- 이 값은 UI 해석 문구 기준이며, `success_90d` 라벨 기준이나 모델 학습 라벨 기준과 분리한다.

## 표본 부족 기준

- `ProjectSettings.market_trend_min_sample`: 장르/태그 trend를 상승으로 해석하기 위한 최소 표본 수이다.
- `ProjectSettings.market_trend_prediction_threshold`, `ProjectSettings.market_trend_success_rate_threshold`, `ProjectSettings.market_flat_prediction_threshold`: 상승/유지/하락 trend 문구를 나누는 리포트 해석 기준이다.
- `ProjectSettings.criteria_genre_min_sample`, `ProjectSettings.criteria_category_min_sample`: 기준표와 결론에 바로 올릴 수 있는 최소 표본 수이다.
- 최소 표본 미만 항목은 숨기지 않고 `탐색 후보 / 표본 부족`으로 분리한다.

## 리뷰 키워드 규칙

- `REVIEW_STOP_WORDS`와 `REVIEW_DOMAIN_TERMS`는 TF-IDF 결과에서 일반 감탄사와 비게임 용어를 줄이고, 발표 가능한 게임 경험 키워드를 남기기 위한 도메인 stopword/allowlist이다.

## 시장 인사이트 도메인 규칙

- `GENRE_LIKE_TAGS`: Steam 태그 중 실제 장르처럼 기획 입력에서 선택해야 하는 항목을 장르 그룹에 합치기 위한 allowlist이다. Steam 원천 데이터는 `genres`와 `steam_tags` 경계가 느슨하므로, RPG·Roguelike·Visual Novel처럼 사용자가 장르로 이해하는 태그를 메인 장르/세부 장르 입력에서 검색할 수 있게 둔다.
- `STRATEGY_TAG_NAMES`: `Indie`, `Free to Play`, `Early Access`처럼 장르가 아니라 출시/사업 전략을 나타내는 태그를 별도 그룹으로 분리하기 위한 규칙이다. 이 값들은 장르 추천 신호와 섞이면 해석이 흐려지므로 `시장/출시 전략 태그` 입력과 guidance에서 따로 다룬다.
- `NOISY_REVIEW_TERMS`: 리뷰 TF-IDF 결과에 반복적으로 나타나지만 발표 가능한 게임 경험 키워드가 아닌 짧은 감탄사·비영어 파편을 제거하기 위한 최소 noise 목록이다. 본문 분석은 `REVIEW_STOP_WORDS`와 `REVIEW_DOMAIN_TERMS`를 함께 써서 도메인 키워드를 보수적으로 남긴다.
