# 프로젝트 진행 가이드 및 교수님 팀미팅 질문

이 문서는 작업공간 자료(`1조 게임.pdf`, 기말 프로젝트 설명 PDF, FigJam/WBS/역할분담 자료)를 바탕으로 프로젝트 진행에 필요한 결정사항, 코드 아키텍처 방향, 교수님께 확인할 질문을 정리한 파일입니다.

## 현재 확정된 방향

- 주제: 신작 게임의 Steam 출시 성공 가능성 예측 모델
- 문제 정의: 출시 전 또는 출시 초기 정보만으로 Steam 신작 게임의 성공 가능성을 예측할 수 있는가?
- 데이터 조건: 2개 이상 source + 직접 크롤링 데이터 포함
- 주요 데이터:
  - Steam 검색/상점 페이지 크롤링
  - Steam Reviews API
  - Metacritic/OpenCritic 또는 SteamDB/SteamSpy 등 보조 데이터
- 분석 중심:
  - 성공/비성공 분류 모델
  - 변수 중요도 분석
  - 성공 요인 및 출시 전략 인사이트 도출

## 1단계 우선 작업

1. 2025년 Steam 출시 게임 후보 appid를 100개 정도 샘플로 수집
2. 각 게임의 출시일, 가격, 장르, 태그, 리뷰 수, 긍정률 수집 가능 여부 확인
3. 수집 성공률과 누락률 기록
4. 문제가 없으면 500~2000개 범위로 확장
5. 출시 후 7일/30일/90일 리뷰 수와 긍정률 계산
6. 흥행/비흥행 라벨 생성
7. 분류 모델을 적용해 성공 가능성이 높은 게임의 특징 분석

## 데이터 수집 설계

### Steam 검색 페이지 크롤링

- 목적: 2025년 출시 게임 후보 appid 확보
- 장점: 전체 Steam 앱을 무작정 수집하지 않아도 됨
- 주의: HTML 구조 변경, 요청 제한, 지역/언어 차이
- 권장 설정: `cc=US`, `l=english` 등 기준 고정

### Steam Store appdetails

- 목적: 기본 상점 정보 수집
- 수집 후보: type, name, is_free, price_overview, release_date, genres, categories, developers, publishers, platforms, metacritic, recommendations
- 주의: 유저 태그는 충분히 제공되지 않을 수 있음

### Steam Reviews API

- 목적: 흥행 대체 지표 생성
- 수집 후보: total_reviews, total_positive, total_negative, review_score_desc, timestamp_created, voted_up, playtime_at_review
- 파생 변수:
  - 긍정률
  - 출시 후 7일/30일/90일 리뷰 수
  - 7일/30일/90일 긍정률
  - 리뷰 증가량

### 보조 데이터

- SteamDB/SteamSpy: 판매량 또는 보유자 수 추정치 보조
- Metacritic/OpenCritic: 외부 평점 보조
- RAWG/IGDB: 장르, 플랫폼, 출시일, 외부 ID 보강
- IsThereAnyDeal: 가격/할인 이력 보강

## 코드 아키텍처 방향

권장 구조는 수집, 전처리, 피처 생성, 모델링, 시각화를 분리하는 방식입니다.

```text
src/
├── collect/
│   ├── steam_search.py
│   ├── steam_appdetails.py
│   ├── steam_reviews.py
│   └── external_sources.py
├── preprocess/
│   ├── clean_games.py
│   ├── merge_sources.py
│   └── make_labels.py
├── features/
│   └── build_features.py
├── models/
│   ├── train.py
│   └── evaluate.py
└── visualize/
    └── charts.py
```

데이터 흐름은 `raw -> interim -> processed -> model outputs -> reports` 순서로 고정합니다. 원천 데이터는 수정하지 않고, 전처리 결과와 학습용 데이터는 별도 파일로 저장하는 것이 좋습니다.

## 모델링 시 주의사항

- 출시 전 예측 모델과 출시 초기 예측 모델을 구분해야 합니다.
- 출시 전 모델 입력에는 출시 후 90일 리뷰 수, 현재 리뷰 수처럼 결과를 미리 알려주는 변수를 넣으면 안 됩니다.
- 리뷰 수 기준은 장르별 편차가 커질 수 있으므로 절대 기준과 장르 내 상대 기준을 모두 비교하는 것이 좋습니다.
- 라벨 불균형이 심하면 F1-score, Precision, Recall 중심으로 평가합니다.

## 교수님 팀미팅 질문

1. 최종 제출물에 코드, 데이터, 보고서, 발표자료, 실행 영상이 모두 포함되어야 하는지
2. GitHub 저장소 제출 또는 공유 방식이 허용되는지
3. 직접 크롤링 데이터의 최소 규모나 인정 기준이 있는지
4. 2개 이상 데이터 source 기준에서 Steam 상점 크롤링과 Steam Reviews API를 별도 source로 인정할 수 있는지
5. Metacritic/OpenCritic/SteamDB 같은 외부 보조 데이터가 일부만 수집되어도 source로 인정되는지
6. 흥행 성공 기준을 리뷰 수와 긍정률로 정의해도 되는지
7. 장르별 편차 보정을 위해 장르 내 상위 25% 같은 상대 기준을 사용해도 되는지
8. 모델 고도화 중심과 시스템 중심 중 평가상 차이가 있는지
9. 분류 외에 클러스터링 또는 네트워크 분석을 반드시 포함해야 하는지, 아니면 선택인지
10. 수업에서 배운 분석 방법 외 scikit-learn 기반 모델을 추가로 사용해도 되는지
11. WBS와 FigJam은 최종 제출물에도 포함해야 하는지
12. Classum 진행 상황 공유 빈도와 형식에 기준이 있는지
13. 팀원별 기여도 평가 방식이 있는지
14. 최종 발표 여부, 발표 시간, 보고서 분량 기준이 있는지
15. 원천 데이터 파일을 함께 제출해야 하는지, 크롤링 코드와 수집 로그만 제출해도 되는지

## 현재 자료에서 확인한 일정

- 1주차: 주제 확정, 데이터 소스 조사, 크롤링 설계
- 2주차: 데이터 수집 및 정제
- 3주차: EDA 및 분석 모델 적용
- 4주차: 결과 해석, 시각화, 발표자료/보고서 작성
- 최종 제출 마감: 6월 15일 자정
- 기말고사: 6월 19일 1-2교시
