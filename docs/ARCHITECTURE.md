# 프로그램 아키텍처 문서

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
