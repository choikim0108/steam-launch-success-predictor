from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from pypdf import PdfReader

from steam_success.config import SETTINGS, settings_table


def _records(data: pd.DataFrame) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], data.to_dict(orient="records"))


def _as_int(value: object) -> int:
    return int(float(str(value)))


def _as_float(value: object) -> float:
    return float(str(value))


def steam_store_url(appid: int) -> str:
    return f"https://store.steampowered.com/app/{appid}/"


def top_predicted_game(reports_dir: Path) -> dict[str, object]:
    predictions_path = reports_dir / "predictions.csv"
    if not predictions_path.exists():
        return {}
    predictions = pd.read_csv(predictions_path).sort_values("predicted_success_probability", ascending=False)
    if predictions.empty:
        return {}
    row = predictions.iloc[0].to_dict()
    appid = int(row["appid"])
    return {
        "appid": appid,
        "name": str(row["name"]),
        "success": int(row["success"]),
        "total_reviews": int(row["total_reviews"]),
        "positive_rate": float(row["positive_rate"]),
        "predicted_success_probability": float(row["predicted_success_probability"]),
        "steam_url": steam_store_url(appid),
    }


def _review_topic_lines(reports_dir: Path) -> list[str]:
    path = reports_dir / "review_topic_summary.csv"
    if not path.exists():
        return ["- 리뷰 토픽 분석 결과가 아직 생성되지 않았다."]
    table = pd.read_csv(path)
    if table.empty:
        return ["- 리뷰 텍스트 표본이 부족해 토픽을 추출하지 못했다."]
    lines: list[str] = []
    for row in _records(table):
        lines.append(f"- {row['genre']} / {row['game_success']} 게임 / {row['review_sentiment']} 리뷰: {row['top_terms']} (리뷰 {_as_int(row['review_count'])}개)")
    return lines


def _service_market_conclusion(reports_dir: Path) -> str:
    path = reports_dir / "review_topic_summary.csv"
    if not path.exists():
        return "리뷰 토픽 분석 결과가 부족해 서비스 개선과 시장 분석 결론을 만들 수 없다."
    table = pd.read_csv(path)
    if table.empty:
        return "리뷰 텍스트 표본이 부족해 서비스 개선과 시장 분석 결론을 만들 수 없다."
    positive_source = cast(pd.DataFrame, table[(table["game_success"] == "success") & (table["review_sentiment"] == "positive")])
    positive = positive_source.head(3)
    negative_source = cast(pd.DataFrame, table[table["review_sentiment"] == "negative"])
    negative = negative_source.sort_values(by=["review_count"], ascending=False).head(3)
    positive_terms = "; ".join(f"{row['genre']}: {row['top_terms']}" for row in _records(positive)) or "데이터 부족"
    negative_terms = "; ".join(f"{row['genre']}: {row['top_terms']}" for row in _records(negative)) or "데이터 부족"
    return f"시장 분석에서는 성공확률 상위 장르의 긍정 키워드({positive_terms})를 신작 포지셔닝 메시지와 Steam 태그 전략에 반영하는 것이 우선이다. 서비스 개선에서는 성공/실패 게임의 부정 키워드({negative_terms})를 출시 직후 패치, 튜토리얼, 밸런스, 콘텐츠 보강 우선순위로 관리해야 한다."


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
- 인터랙티브 HTML 리포트: `reports/interactive_report.html`
- 시각화 이미지: `reports/figures/`
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
├── reporting.py              # PDF 요약, 아키텍처/메모/결론 문서 생성
├── web_report.py             # HTML 리포트 생성
└── pipeline.py               # 전체 파이프라인 실행 진입점
```

## 데이터 흐름
1. `collect`: Steam 검색 결과 페이지를 직접 크롤링해 appid 후보를 만든다.
2. `collect`: appid별 상점 상세정보와 리뷰 요약을 API로 수집한다.
3. `preprocess`: HTML 크롤링 데이터, appdetails, review summary를 병합한다.
4. `preprocess`: `total_reviews >= 500` 및 `positive_rate >= 0.80`이면 성공으로 라벨링한다.
5. `features`: 출시 전/초기에도 알 수 있는 가격, 장르 수, 카테고리 수, 언어 수, 플랫폼, 멀티플레이 여부 등을 입력 변수로 만든다.
6. `models`: Logistic Regression과 Random Forest를 비교하고 F1 중심으로 최적 모델을 저장한다.
7. `visualize`: 라벨 분포, 리뷰-긍정률 산점도, 변수 중요도, 작업 흐름 도식 PNG를 생성한다.
8. `reporting/web_report`: Markdown 결론과 HTML 리포트에 "그래서 성공할 것으로 예측되는 게임" 답변을 포함한다.

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


def write_workspace_docs_index(root: Path, docs_dir: Path) -> None:
    text = f"""# 문서 및 경로 정리

## 먼저 읽을 문서
- `AGENTS.md`: 에이전트 작업 전 필수 규칙
- `README.md`: 프로젝트 목적, 데이터 계획, 성공 기준
- `docs/MANUAL.md`: 실행 방법과 산출물 위치

## 주요 경로
- `src/steam_success/`: 크롤링, 전처리, 피처, 모델링, 시각화, 리포트 생성 코드
- `data/raw/`: Steam 검색 HTML, Store API, Reviews API 원천 수집 결과
- `data/interim/`: 병합된 중간 데이터
- `data/processed/`: 모델 학습용 데이터
- `reports/`: CSV/JSON 평가 결과, 결론 Markdown, HTML 리포트
- `reports/figures/`: HTML에 포함되는 최신 PNG 시각화
- `models/`: 학습된 모델 파일
- `docs/`: 프로젝트 설명, 아키텍처, 실행 매뉴얼, 가정/질문, PDF 요약

## 작업공간 루트 참고 자료
- `{root.parent.name}/1조 게임 (1).pdf`: 팀 프로젝트 참고 PDF
- `{root.parent.name}/20260518_[데이터마이닝] 2026기말프로젝트.pdf`: 과제 설명 PDF
- `{root.parent.name}/WBS_초안_주제1_주제4.md` 및 CSV/XLSX 파일: 초기 일정/역할/브레인스토밍 자료

루트의 원본 과제 자료는 제출/참고 경로가 바뀌지 않도록 이동하지 않는다. 프로젝트 내부 산출물 문서는 `docs/`와 `reports/`로 구분해 관리한다.
"""
    (docs_dir / "WORKSPACE_DOCUMENTS.md").write_text(text, encoding="utf-8")


def write_run_summary(reports_dir: Path, dataset: pd.DataFrame, result: dict[str, object], chart_paths: list[Path]) -> None:
    metrics = pd.read_csv(reports_dir / "model_metrics.csv")
    best_row = metrics.sort_values(["f1", "recall", "accuracy"], ascending=False).iloc[0].to_dict()
    top_features = pd.read_csv(reports_dir / "feature_importance.csv").head(8)
    text = [
        "# Steam 출시 성공 예측 모델 실행 결과",
        "",
        f"- 모델링 데이터 수: {len(dataset)}",
        f"- 성공 라벨 수: {len(dataset[dataset['success'] == 1])}",
        f"- 비성공 라벨 수: {len(dataset[dataset['success'] == 0])}",
        f"- 선택 모델: {result.get('best_model')}",
        f"- 테스트 Accuracy: {best_row.get('accuracy'):.3f}",
        f"- 테스트 Precision: {best_row.get('precision'):.3f}",
        f"- 테스트 Recall: {best_row.get('recall'):.3f}",
        f"- 테스트 F1: {best_row.get('f1'):.3f}",
        "",
        "## 주요 피처 중요도",
    ]
    text += [f"- {row['feature']}: {_as_float(row['importance']):.4f}" for row in _records(top_features)]
    criteria_tables = build_criteria_tables(dataset)
    predicted_game = top_predicted_game(reports_dir)
    genre_summary = criteria_tables["genre"]
    for name, table in criteria_tables.items():
        table.to_csv(reports_dir / f"criteria_{name}.csv", index=False)
    conclusion_path = reports_dir / "CONCLUSIONS.md"
    write_conclusions_doc(conclusion_path, dataset, best_row, criteria_tables, predicted_game)
    if predicted_game:
        text += [
            "",
            "## 그래서 성공할 것으로 예측되는 게임",
            f"- [{predicted_game['name']}]({predicted_game['steam_url']})",
            f"- 예측 성공 확률: {_as_float(predicted_game['predicted_success_probability']):.1%}",
            f"- 현재 성공 기준 충족 여부: {'충족' if predicted_game['success'] else '미충족'}",
            f"- 리뷰 수/긍정률: {_as_int(predicted_game['total_reviews']):,}개 / {_as_float(predicted_game['positive_rate']):.1%}",
        ]
    text += ["", "## 성공확률 상위 장르 리뷰 토픽 분석"]
    text += _review_topic_lines(reports_dir)
    text += ["", "## 서비스 개선 및 시장 분석 결론", _service_market_conclusion(reports_dir)]
    text += ["", "## 장르별 결론 상위 항목"]
    text += [f"- {row['criteria_value']}: 성공 {_as_int(row['success_count'])}개 / 전체 {_as_int(row['game_count'])}개, 성공률 {_as_float(row['success_rate']):.1%} (n={_as_int(row['game_count'])})" for row in _records(_rank_eligible_rows(genre_summary).head(8))]
    text += ["", "## 생성 차트"]
    text += [f"- `{path.relative_to(reports_dir.parent)}`" for path in chart_paths]
    text += ["", "## 결론 위치", "- 상세 결론과 해석 주의사항은 `reports/CONCLUSIONS.md`에 저장했다."]
    text += ["", "## 해석 주의", "- 이 결과는 Steam `popularnew` 검색 노출 샘플 기반이므로 전체 Steam 시장의 무작위 표본은 아니다. 성공/실패 비율은 모델 학습용 라벨 분포이지 실제 시장 성공률로 해석하면 안 된다."]
    (reports_dir / "RUN_SUMMARY.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def build_criteria_tables(dataset: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "genre": _exploded_success_summary(dataset, "genres", "genre"),
        "category": _exploded_success_summary(dataset, "categories", "category"),
        "price_band": _binned_success_summary(dataset, "price_final_usd", "price_band", [-0.01, 0, 10, 30, 60, np.inf], ["free", "under_10", "10_to_30", "30_to_60", "60_plus"]),
        "language_band": _binned_success_summary(dataset, "supported_language_count", "language_band", [-1, 5, 15, 30, np.inf], ["1_5", "6_15", "16_30", "31_plus"]),
        "platform_count": _platform_success_summary(dataset),
        "multiplayer": _boolean_success_summary(dataset, "has_multiplayer", "multiplayer"),
        "external_attention": _binned_success_summary(dataset, "external_attention_score", "external_attention", [-1, 0, 5, 15, np.inf], ["none", "low", "medium", "high"]),
    }


def _success_summary(data: pd.DataFrame, criteria_name: str, value_col: str) -> pd.DataFrame:
    columns = ["criteria", "criteria_value", "game_count", "success_count", "success_rate", "smoothed_success_rate", "sample_status", "rank_eligible"]
    if data.empty:
        return pd.DataFrame(columns=columns)
    summary = cast(pd.DataFrame, data.groupby(value_col, as_index=False).agg(game_count=("success", "size"), success_count=("success", "sum")))
    summary["success_rate"] = summary["success_count"] / summary["game_count"]
    global_rate = float(data["success"].mean()) if len(data) else 0.0
    summary["smoothed_success_rate"] = (summary["success_count"] + SETTINGS.criteria_smoothing_alpha * global_rate) / (summary["game_count"] + SETTINGS.criteria_smoothing_alpha)
    minimum = _criteria_min_sample(criteria_name)
    summary["rank_eligible"] = summary["game_count"] >= minimum
    summary["sample_status"] = summary["rank_eligible"].map(lambda eligible: "충분" if bool(eligible) else "표본 부족")
    summary.insert(0, "criteria", criteria_name)
    summary = cast(pd.DataFrame, summary.rename(columns={value_col: "criteria_value"}))
    return summary.sort_values(by=["rank_eligible", "smoothed_success_rate", "success_count", "game_count"], ascending=False)


def _criteria_min_sample(criteria_name: str) -> int:
    if criteria_name == "genre":
        return SETTINGS.criteria_genre_min_sample
    if criteria_name == "category":
        return SETTINGS.criteria_category_min_sample
    return 1


def _exploded_success_summary(dataset: pd.DataFrame, column: str, criteria_name: str) -> pd.DataFrame:
    rows = []
    for row in _records(cast(pd.DataFrame, dataset[[column, "success"]])):
        values = _split_criteria_values(row[column])
        for value in values:
            rows.append({criteria_name: value, "success": _as_int(row["success"])})
    data = pd.DataFrame(rows)
    if data.empty:
        return _success_summary(data, criteria_name, criteria_name)
    return _success_summary(data, criteria_name, criteria_name)


def _split_criteria_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, float) and np.isnan(value):
        return []
    return [part.strip() for part in str(value).split(",") if part.strip() and part.strip().lower() != "nan"]


def _binned_success_summary(dataset: pd.DataFrame, column: str, criteria_name: str, bins: list[float], labels: list[str]) -> pd.DataFrame:
    data = cast(pd.DataFrame, dataset[[column, "success"]].copy())
    values = cast(pd.Series, data[column]).fillna(0)
    data[criteria_name] = pd.Series(pd.cut(values, bins=bins, labels=labels), index=data.index).astype(str)
    return _success_summary(data, criteria_name, criteria_name)


def _boolean_success_summary(dataset: pd.DataFrame, column: str, criteria_name: str) -> pd.DataFrame:
    data = cast(pd.DataFrame, dataset[[column, "success"]].copy())
    data[criteria_name] = cast(pd.Series, data[column]).map(lambda value: "yes" if bool(value) else "no").fillna("unknown")
    return _success_summary(data, criteria_name, criteria_name)


def _platform_success_summary(dataset: pd.DataFrame) -> pd.DataFrame:
    data = cast(pd.DataFrame, dataset[["platform_windows", "platform_mac", "platform_linux", "success"]].copy())
    data["platform_count"] = data[["platform_windows", "platform_mac", "platform_linux"]].sum(axis=1).astype(int).astype(str) + " platforms"
    return _success_summary(data, "platform_count", "platform_count")


def _criteria_markdown(criteria_tables: dict[str, pd.DataFrame]) -> str:
    labels = {
        "category": "상점 기능/카테고리",
        "price_band": "가격대",
        "language_band": "지원 언어 수",
        "platform_count": "지원 플랫폼 수",
        "multiplayer": "멀티플레이 여부",
        "external_attention": "외부 웹 관심도",
    }
    lines: list[str] = []
    for key, title in labels.items():
        table = _rank_eligible_rows(criteria_tables[key]).head(5)
        lines.append(f"### {title}")
        if table.empty:
            lines.append("- 분석 가능한 항목이 부족함")
        else:
            lines.extend([
                f"- {row['criteria_value']}: 성공 {_as_int(row['success_count'])}개 / 전체 {_as_int(row['game_count'])}개, 성공률 {_as_float(row['success_rate']):.1%}"
                for row in _records(table)
            ])
        lines.append("")
    return "\n".join(lines).strip()



def _rank_eligible_rows(table: pd.DataFrame) -> pd.DataFrame:
    if table.empty or "rank_eligible" not in table.columns:
        return table
    mask = cast(pd.Series, table["rank_eligible"]).map(_truthy)
    return cast(pd.DataFrame, table[mask])


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}

def write_conclusions_doc(output_path: Path, dataset: pd.DataFrame, best_row: dict[str, object], criteria_tables: dict[str, pd.DataFrame], predicted_game: dict[str, object]) -> None:
    total = len(dataset)
    success_count = len(dataset[dataset["success"] == 1])
    failure_count = len(dataset[dataset["success"] == 0])
    success_rate = success_count / total if total else 0
    genre_summary = criteria_tables["genre"]
    top_genres = [
        f"- {row['criteria_value']}: 성공 {_as_int(row['success_count'])}개 / 전체 {_as_int(row['game_count'])}개, 성공률 {_as_float(row['success_rate']):.1%} (n={_as_int(row['game_count'])})"
        for row in _records(_rank_eligible_rows(genre_summary).head(10))
    ]
    if not top_genres:
        top_genres = [f"- 장르별 표본이 부족해 최소 {SETTINGS.criteria_genre_min_sample}개 이상 등장한 장르 기준 결론을 만들 수 없음."]
    raw_accuracy = best_row.get("accuracy")
    raw_f1 = best_row.get("f1")
    accuracy = raw_accuracy if isinstance(raw_accuracy, float | int) else 0.0
    f1 = raw_f1 if isinstance(raw_f1, float | int) else 0.0
    if predicted_game:
        predicted_answer = f"""현재 모델이 가장 성공 가능성이 높다고 예측한 게임은 [{predicted_game['name']}]({predicted_game['steam_url']})이다. 예측 성공 확률은 {_as_float(predicted_game['predicted_success_probability']):.1%}이며, 현재 수집 기준에서는 리뷰 {_as_int(predicted_game['total_reviews']):,}개와 긍정률 {_as_float(predicted_game['positive_rate']):.1%}로 성공 기준을 {'충족' if predicted_game['success'] else '충족하지 못했다'}."""
    else:
        predicted_answer = "예측 결과 파일이 없어 특정 게임을 지목할 수 없다."
    text = f"""# 실제 결론 및 해석

## 핵심 결론
이번 수집 데이터에서는 성공 라벨이 {success_count}개, 비성공 라벨이 {failure_count}개이며 성공 라벨 비율은 {success_rate:.1%}이다. 이 비율은 Steam 전체 시장 성공률이 아니라 `popularnew` 검색 결과에서 수집된 표본과 현재 성공 기준에 따른 학습용 라벨 분포다.

## 그래서 성공할 것으로 예측되는 게임은 뭔가?
{predicted_answer}

## 성공 게임이 많이 나타난 장르
{chr(10).join(top_genres)}

## 다양한 기준별 결과
{_criteria_markdown(criteria_tables)}

## 성공확률 상위 장르의 성공/실패 게임 리뷰 토픽
{chr(10).join(_review_topic_lines(output_path.parent))}

## 게임 서비스 개선 및 시장 분석 결론
{_service_market_conclusion(output_path.parent)}

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
