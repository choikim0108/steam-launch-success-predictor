# 프로젝트 상태 점검 및 레거시 정리

## 현재 브랜치 상태

- 작업 브랜치: `yongwoo`
- 기준 브랜치: `main`
- 목적: 데이터 수집과 90일 성공 예측 파이프라인 준비

## 정리 결론

현재 저장소에는 두 흐름이 섞여 있었다.

```text
레거시 흐름:
현재 누적 리뷰 수와 현재 긍정률로 성공 라벨을 만들고 모델을 학습

신규 확정 흐름:
출시 7일 이내 데이터로 출시 90일 성공 여부를 예측
```

레거시 흐름은 초기 작동 모델과 보고서 생성에는 유용했지만, 최종 주제인 "출시 초기 데이터 기반 90일 성공 예측"과는 기준이 다르다. 따라서 기존 실행 결과 산출물은 루트 `reports/`와 `models/`에서 치우고 `legacy/current_snapshot/`에 보존했다.

## 레거시로 분리한 산출물

아래 파일들은 과거 현재 누적 리뷰 기준 실행 결과다.

```text
legacy/current_snapshot/reports/RUN_SUMMARY.md
legacy/current_snapshot/reports/CONCLUSIONS.md
legacy/current_snapshot/reports/model_metrics.json
legacy/current_snapshot/reports/interactive_report.html
legacy/current_snapshot/models/steam_success_model.joblib
legacy/current_snapshot/docs/ARCHITECTURE.md
legacy/current_snapshot/docs/ASSUMPTIONS_AND_QUESTIONS.md
```

이 파일들은 참고용으로만 사용한다. 최종 모델 성능이나 최종 결론으로 사용하지 않는다.

## 현재 유지하는 산출물

아래 파일들은 신규 방향 설정과 데이터 수집 준비에 필요하므로 유지한다.

```text
docs/DATA_COLLECTION_RUNBOOK.md
docs/reference/DEVELOPER_AND_USER_EXPERIENCE.md
docs/TEAM_PROJECT_PLAN.md
reports/90d/market_insight_site.html
reports/90d/interactive_report.html
```

## 아직 레거시 기준이 남아 있는 코드

다음 코드는 아직 현재 누적 리뷰 기준을 사용한다.

```text
src/steam_success/preprocess/dataset.py
- total_reviews >= 500
- positive_rate >= 0.80
- success 컬럼 생성

src/steam_success/features/build_features.py
- success 컬럼을 y로 사용

src/steam_success/models/train.py
- predictions.csv에 total_reviews, positive_rate 포함

src/steam_success/reporting.py
src/steam_success/web_report.py
src/steam_success/visualize/charts.py
- 현재 success 기준 보고서 생성
```

이 코드는 바로 삭제하지 않는다. 다음 작업에서 `success_90d` 기반 전처리와 모델링이 준비되면 교체하거나 `legacy` 모듈로 분리한다.

## 신규 기준으로 확정한 작업 방향

```text
1. appid 후보 수집
2. appdetails 수집
3. 리뷰별 timestamp_created, voted_up 수집
4. release_date 기준 days_since_release 계산
5. reviews_7d, positive_rate_7d 생성
6. reviews_30d, positive_rate_30d 생성
7. reviews_90d, positive_rate_90d 생성
8. success_90d 라벨 생성
9. 출시 7일 이내 feature만 사용해 90일 성공 예측 모델 학습
```

## 다음 작업 전 체크리스트

- `release_date_text` 파싱 함수 추가
- 리뷰 타임라인과 appdetails 병합
- 90일 미만 출시작 제외 로직 추가
- `success_90d` 생성
- feature 목록에서 미래 결과 변수 제거
- 기존 `success` 기준 보고서가 새 결과와 섞이지 않도록 출력 파일명 변경
- 기본 수집은 `steam_success.collect.base`를 사용하고, 레거시 `steam_success.pipeline` 실행을 피하기

## 작업 원칙

```text
현재 누적 성과 지표:
현재 성과 비교/보조 분석에만 사용

출시 7일 이내 지표:
예측 모델 입력으로 사용 가능

출시 90일 지표:
정답 라벨 생성에만 사용
```
