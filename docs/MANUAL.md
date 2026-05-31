# 매뉴얼 실행 방법

## 1. 실행 준비
프로젝트 폴더로 이동한다.

```bash
cd steam-launch-success-predictor
```

필요 라이브러리는 `requirements.txt`에 정리되어 있다. 새 환경에서는 아래처럼 설치한다.

```bash
python3 -m pip install --user --break-system-packages -r requirements.txt
```

## 2. 기본 데이터 수집
아래 명령은 모델 학습 없이 Steam appid, appdetails, 리뷰 요약만 수집한다.

```bash
PYTHONPATH=src python3 -m steam_success.collect.base
```

## 3. 샘플 수만 임시 변경해서 수집
설정 파일을 고치지 않고 한 번만 샘플 수를 바꾸려면 아래처럼 실행한다.

```bash
PYTHONPATH=src python3 -m steam_success.collect.base --max-apps 250
```

기존 `run_pipeline.py`와 `steam_success.pipeline`은 현재 누적 리뷰 기준의 초기 작동 모델 흐름이므로, 90일 예측 데이터 수집 단계에서는 사용하지 않는다.

## 4. 변수값 변경 위치
모델 수, 샘플 수, 성공 기준, 테스트 비율, 랜덤시드 등 주요 변수는 모두 `src/steam_success/config.py`의 `ProjectSettings`에 모아두었다.

| 변수 | 현재 값 |
| --- | --- |
| max_apps | `180` |
| search_pages | `8` |
| request_sleep_seconds | `0.2` |
| external_signal_sample_size | `12` |
| external_request_sleep_seconds | `0.15` |
| review_text_sample_size | `24` |
| review_texts_per_game | `20` |
| review_timeline_page_size | `100` |
| review_timeline_max_reviews_per_game | `500` |
| country | `US` |
| language | `english` |
| youtube_search_domain | `youtube.com` |
| webzine_domains | `('ign.com', 'pcgamer.com', 'gamespot.com', 'rockpapershotgun.com')` |
| blog_domains | `('medium.com', 'substack.com', 'wordpress.com', 'blogspot.com')` |
| success_review_threshold | `500` |
| success_positive_rate_threshold | `0.8` |
| random_state | `42` |
| test_size_large_sample | `0.3` |
| test_size_small_sample | `0.4` |
| small_sample_cutoff | `20` |
| use_logistic_regression | `True` |
| use_random_forest | `True` |
| logistic_max_iter | `1000` |
| random_forest_n_estimators | `300` |
| random_forest_max_depth | `6` |
| random_forest_min_samples_leaf | `2` |

## 5. 결과 확인 위치

주의: 기존 현재 누적 리뷰 기준으로 생성된 초기 실행 결과는 `legacy/current_snapshot/`에 보존했다. 아래 경로는 파이프라인을 다시 실행하면 새로 생성되는 산출물 위치다.

- 최종 실행 요약: `reports/RUN_SUMMARY.md`
- 장르별 결론: `reports/CONCLUSIONS.md`
- 모델 성능표: `reports/model_metrics.csv`
- 게임별 예측 확률: `reports/predictions.csv`
- 인터랙티브 HTML 리포트: `reports/interactive_report.html`
- 시각화 이미지: `reports/figures/`
- 학습 데이터: `data/processed/modeling_dataset.csv`
- 저장 모델: `models/steam_success_model.joblib`

## 6. 리뷰 timestamp 타임라인 수집
출시 7일/30일/90일 리뷰 지표를 만들려면 리뷰 요약이 아니라 리뷰별 `timestamp_created`가 필요하다. 기존 수집으로 `data/raw/steam_search_crawl.csv`를 만든 뒤 아래 명령을 실행한다.

```bash
PYTHONPATH=src python3 -m steam_success.collect.review_timeline --max-apps 50 --max-reviews-per-game 500
```

Windows PowerShell에서는 아래처럼 실행한다.

```powershell
$env:PYTHONPATH="src"
python -m steam_success.collect.review_timeline --max-apps 50 --max-reviews-per-game 500
```

결과는 `data/raw/steam_review_timeline.csv`와 `data/raw/review_timeline/`에 저장된다.
