from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from steam_success.config import SETTINGS, settings_table


def summarize_pdf(pdf_path: Path, output_path: Path) -> None:
    lines = ["# PDF 참고 내용 요약", ""]
    if not pdf_path.exists():
        lines += [f"- PDF 파일을 찾지 못함: `{pdf_path}`"]
    else:
        reader = PdfReader(str(pdf_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        keywords = ["Steam", "스팀", "게임", "성공", "리뷰", "판매", "크롤링", "모델", "데이터"]
        picked = []
        for raw in text.splitlines():
            line = " ".join(raw.split())
            if 20 <= len(line) <= 180 and any(k.lower() in line.lower() for k in keywords):
                picked.append(line)
            if len(picked) >= 25:
                break
        lines += [f"- 원본: `{pdf_path.name}`", f"- 추출 페이지 수: {len(reader.pages)}", "", "## 관련 문장 발췌"]
        lines += [f"- {line}" for line in picked] if picked else ["- 자동 추출 가능한 관련 문장이 적어 기존 README/가이드의 주제 정의를 우선 참고함."]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manual_doc(docs_dir: Path) -> None:
    settings_lines = [f"| {name} | `{value}` |" for name, value in settings_table()]
    text = """# 매뉴얼 실행 방법

## 1. 실행 준비
프로젝트 폴더로 이동한다.

```bash
cd steam-launch-success-predictor
```

필요 라이브러리는 `requirements.txt`에 정리되어 있다. 새 환경에서는 아래처럼 설치한다.

```bash
python3 -m pip install --user --break-system-packages -r requirements.txt
```

## 2. 기본 실행
아래 명령은 `src/steam_success/config.py`의 `SETTINGS.max_apps` 값을 사용한다.

```bash
PYTHONPATH=src python3 run_pipeline.py
```

## 3. 샘플 수만 임시 변경해서 실행
설정 파일을 고치지 않고 한 번만 샘플 수를 바꾸려면 아래처럼 실행한다.

```bash
PYTHONPATH=src python3 -m steam_success.pipeline --max-apps 250
```

## 4. 변수값 변경 위치
모델 수, 샘플 수, 성공 기준, 테스트 비율, 랜덤시드 등 주요 변수는 모두 `src/steam_success/config.py`의 `ProjectSettings`에 모아두었다.

| 변수 | 현재 값 |
| --- | --- |
""" + "\n".join(settings_lines) + """

## 5. 결과 확인 위치
- 최종 실행 요약: `reports/RUN_SUMMARY.md`
- 장르별 결론: `reports/CONCLUSIONS.md`
- 모델 성능표: `reports/model_metrics.csv`
- 게임별 예측 확률: `reports/predictions.csv`
- 학습 데이터: `data/processed/modeling_dataset.csv`
- 저장 모델: `models/steam_success_model.joblib`
"""
    (docs_dir / "MANUAL.md").write_text(text, encoding="utf-8")


def write_architecture_doc(docs_dir: Path) -> None:
    text = """# 프로그램 아키텍처 문서

## 목적
Steam 상점에서 새로 출시된 게임 후보를 직접 크롤링하고, Steam Store API와 Steam Reviews API로 보강한 뒤, 출시 성공 가능성을 분류 모델로 예측한다.

## 사용 언어와 라이브러리
- 언어: Python 3.12
- 데이터 수집: requests, beautifulsoup4, lxml
- 데이터 처리: pandas, numpy
- 모델링: scikit-learn, joblib
- 시각화: matplotlib
- PDF 참고 추출: pypdf

## 모듈 구조
```text
src/steam_success/
├── collect/steam.py          # Steam 검색 HTML 크롤링, appdetails/reviews API 수집
├── preprocess/dataset.py     # 수집 데이터 병합, 결측 처리, 성공 라벨 생성
├── features/build_features.py# 모델 입력 피처 목록과 X/y 생성
├── models/train.py           # Logistic Regression, Random Forest 학습/평가
├── visualize/charts.py       # 라벨/리뷰/중요도 차트 생성
├── reporting.py              # PDF 요약, 아키텍처/메모 문서 생성
└── pipeline.py               # 전체 파이프라인 실행 진입점
```

## 데이터 흐름
1. `collect`: Steam 검색 결과 페이지를 직접 크롤링해 appid 후보를 만든다.
2. `collect`: appid별 상점 상세정보와 리뷰 요약을 API로 수집한다.
3. `preprocess`: HTML 크롤링 데이터, appdetails, review summary를 병합한다.
4. `preprocess`: `total_reviews >= 500` 및 `positive_rate >= 0.80`이면 성공으로 라벨링한다.
5. `features`: 출시 전/초기에도 알 수 있는 가격, 장르 수, 카테고리 수, 언어 수, 플랫폼, 멀티플레이 여부 등을 입력 변수로 만든다.
6. `models`: Logistic Regression과 Random Forest를 비교하고 F1 중심으로 최적 모델을 저장한다.
7. `visualize/reporting`: 결과 CSV, JSON, PNG, 문서 산출물을 생성한다.

## 산출물 위치
- 원천 데이터: `data/raw/`
- 병합/정제 데이터: `data/interim/`
- 모델 학습 데이터: `data/processed/`
- 학습 모델: `models/steam_success_model.joblib`
- 평가/예측/차트: `reports/`
- 아키텍처/메모/PDF 요약: `docs/`

## 유지보수 기준
수집, 전처리, 피처, 모델, 시각화, 문서 생성을 서로 다른 모듈로 분리했다. Steam HTML 구조가 바뀌면 `collect/steam.py`, 성공 기준이나 모델 변수값이 바뀌면 `config.py`의 `ProjectSettings`를 우선 수정하면 된다.
"""
    (docs_dir / "ARCHITECTURE.md").write_text(text, encoding="utf-8")


def write_assumptions_doc(docs_dir: Path, dataset: pd.DataFrame, result: dict[str, object]) -> None:
    counts = dataset["success"].value_counts().to_dict()
    text = f"""# 모델 구축 메모 및 교수님 확인 질문

## 임의로 정한 기준
- 성공 기준: 전체 리뷰 수 {SETTINGS.success_review_threshold:,}개 이상이고 긍정률 {SETTINGS.success_positive_rate_threshold:.0%} 이상인 게임을 성공으로 정의했다.
- 기간 기준: Steam Reviews API의 무료 공개 요약은 특정 출시 후 90일 누적치를 안정적으로 직접 제공하지 않으므로, 이번 작동 모델은 현재 시점 누적 리뷰를 성공 대체 지표로 사용했다.
- 예측 입력: 출시 후 결과 변수인 리뷰 수와 긍정률은 라벨 생성에만 사용하고 모델 입력에서는 제외했다.
- 수집 범위: Steam `popularnew` 검색 페이지에서 직접 크롤링한 appid 샘플을 사용했다.

## 실제 수집 데이터와 PDF/초기 기획 차이
- 초기 기획은 출시 후 7/30/90일 리뷰 수를 이상적으로 제안했지만, 이번 구현은 공개 API로 즉시 재현 가능한 현재 누적 리뷰 요약을 사용했다.
- 실제 판매량은 Steam에서 공개하지 않으므로 리뷰 수와 긍정률을 판매 성공의 proxy로 사용했다.

## 이번 실행 요약
- 최종 모델링 데이터 게임 수: {len(dataset)}
- 라벨 분포: {counts}
- 선택 모델: {result.get('best_model')}
- 학습/테스트 크기: {result.get('train_size')} / {result.get('test_size')}

## 교수님께 질문하면 좋은 내용
1. Steam 상점 HTML 크롤링과 Steam Reviews API를 서로 다른 2개 데이터 source로 인정할 수 있는지
2. 실제 판매량이 비공개일 때 리뷰 수와 긍정률을 성공 proxy로 사용하는 것이 적절한지
3. 성공 기준을 절대 기준(리뷰 500개, 긍정률 80%)으로 둘지, 장르/출시연도별 상위 분위수로 둘지
4. 출시 후 90일 내 성공만 성공으로 볼지, 장기적으로 역주행한 게임도 성공으로 볼지
5. 최종 제출 시 원천 HTML/JSON 파일까지 함께 제출해야 하는지

생성 시각: {datetime.now().isoformat(timespec='seconds')}
"""
    (docs_dir / "ASSUMPTIONS_AND_QUESTIONS.md").write_text(text, encoding="utf-8")


def write_run_summary(reports_dir: Path, dataset: pd.DataFrame, result: dict[str, object], chart_paths: list[Path]) -> None:
    metrics = pd.read_csv(reports_dir / "model_metrics.csv")
    best_row = metrics.sort_values(["f1", "recall", "accuracy"], ascending=False).iloc[0].to_dict()
    top_features = pd.read_csv(reports_dir / "feature_importance.csv").head(8)
    text = [
        "# Steam 출시 성공 예측 모델 실행 결과",
        "",
        f"- 모델링 데이터 수: {len(dataset)}",
        f"- 성공 라벨 수: {int(dataset['success'].sum())}",
        f"- 비성공 라벨 수: {int((dataset['success'] == 0).sum())}",
        f"- 선택 모델: {result.get('best_model')}",
        f"- 테스트 Accuracy: {best_row.get('accuracy'):.3f}",
        f"- 테스트 Precision: {best_row.get('precision'):.3f}",
        f"- 테스트 Recall: {best_row.get('recall'):.3f}",
        f"- 테스트 F1: {best_row.get('f1'):.3f}",
        "",
        "## 주요 피처 중요도",
    ]
    text += [f"- {row.feature}: {row.importance:.4f}" for row in top_features.itertuples()]
    genre_summary = _genre_success_summary(dataset)
    conclusion_path = reports_dir / "CONCLUSIONS.md"
    write_conclusions_doc(conclusion_path, dataset, best_row, genre_summary)
    genre_summary.to_csv(reports_dir / "genre_success_summary.csv", index=False)
    text += ["", "## 장르별 결론 상위 항목"]
    text += [
        f"- {row.genre}: 성공 {int(row.success_count)}개 / 전체 {int(row.game_count)}개, 성공률 {row.success_rate:.1%}"
        for row in genre_summary.head(8).itertuples()
    ]
    text += ["", "## 생성 차트"]
    text += [f"- `{path.relative_to(reports_dir.parent)}`" for path in chart_paths]
    text += ["", "## 결론 위치", "- 상세 결론과 해석 주의사항은 `reports/CONCLUSIONS.md`에 저장했다."]
    text += ["", "## 해석 주의", "- 이 결과는 Steam `popularnew` 검색 노출 샘플 기반이므로 전체 Steam 시장의 무작위 표본은 아니다. 성공/실패 비율은 모델 학습용 라벨 분포이지 실제 시장 성공률로 해석하면 안 된다."]
    (reports_dir / "RUN_SUMMARY.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def _genre_success_summary(dataset: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in dataset[["genres", "success"]].itertuples(index=False):
        genres = [part.strip() for part in str(row.genres).split(",") if part.strip()]
        for genre in genres:
            rows.append({"genre": genre, "success": int(row.success)})
    if not rows:
        return pd.DataFrame(columns=["genre", "game_count", "success_count", "success_rate"])
    genre_data = pd.DataFrame(rows)
    summary = genre_data.groupby("genre", as_index=False).agg(game_count=("success", "size"), success_count=("success", "sum"))
    summary["success_rate"] = summary["success_count"] / summary["game_count"]
    return summary[summary["game_count"] >= 3].sort_values(["success_rate", "success_count", "game_count"], ascending=False)


def write_conclusions_doc(output_path: Path, dataset: pd.DataFrame, best_row: dict[str, object], genre_summary: pd.DataFrame) -> None:
    total = len(dataset)
    success_count = int(dataset["success"].sum())
    failure_count = int((dataset["success"] == 0).sum())
    success_rate = success_count / total if total else 0
    top_genres = [
        f"- {row.genre}: 성공 {int(row.success_count)}개 / 전체 {int(row.game_count)}개, 성공률 {row.success_rate:.1%}"
        for row in genre_summary.head(10).itertuples()
    ]
    if not top_genres:
        top_genres = ["- 장르별 표본이 부족해 최소 3개 이상 등장한 장르 기준 결론을 만들 수 없음."]
    raw_accuracy = best_row.get("accuracy")
    raw_f1 = best_row.get("f1")
    accuracy = raw_accuracy if isinstance(raw_accuracy, float | int) else 0.0
    f1 = raw_f1 if isinstance(raw_f1, float | int) else 0.0
    text = f"""# 실제 결론 및 해석

## 핵심 결론
이번 수집 데이터에서는 성공 라벨이 {success_count}개, 비성공 라벨이 {failure_count}개이며 성공 라벨 비율은 {success_rate:.1%}이다. 이 비율은 Steam 전체 시장 성공률이 아니라 `popularnew` 검색 결과에서 수집된 표본과 현재 성공 기준에 따른 학습용 라벨 분포다.

## 성공 게임이 많이 나타난 장르
{chr(10).join(top_genres)}

## 모델 결과 해석
- 선택 모델 기준 테스트 Accuracy는 {accuracy:.3f}, F1은 {f1:.3f}이다.
- F1은 성공/실패 양쪽을 함께 보는 지표라 Accuracy만 보는 것보다 현재 분류 문제에 더 적합하다.
- 현재처럼 성공 {success_count}개/비성공 {failure_count}개로 한쪽이 더 많은 분포는 학습 자체를 막을 수준은 아니지만, 전체 표본 수와 수집 편향 때문에 장르별 결론이 흔들릴 수 있다.

## 유의미성 판단
현재 결과는 '실행 가능한 탐색 모델'로는 유의미하지만, 최종 일반화 결론으로 보기에는 제한이 있다. 이유는 표본이 Steam 전체 무작위 표본이 아니고, 성공 기준이 실제 매출이 아닌 리뷰 수와 긍정률 proxy이기 때문이다. 따라서 보고서에서는 '현재 수집 표본에서는 이런 경향이 보였다'고 표현하는 것이 안전하다.

## 추가 개선 방향
- `src/steam_success/config.py`에서 `max_apps`를 더 늘려 재수집한다.
- 장르별 최소 표본 수를 10개 이상으로 높인 뒤 장르 결론을 다시 해석한다.
- 리뷰 500개/긍정률 80% 기준과 장르별 상위 분위수 기준을 함께 비교한다.
"""
    output_path.write_text(text, encoding="utf-8")
