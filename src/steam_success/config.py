from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class ProjectSettings:
    # 데이터 수집 규모/속도
    max_apps: int = 180
    search_pages: int = 8
    request_sleep_seconds: float = 0.20
    external_signal_sample_size: int = 12
    external_request_sleep_seconds: float = 0.15
    review_text_sample_size: int = 40
    review_texts_per_game: int = 100
    review_timeline_page_size: int = 100
    review_timeline_max_reviews_per_game: int = 500
    country: str = "US"
    language: str = "english"

    # 외부 웹 신호 검색 도메인
    youtube_search_domain: str = "youtube.com"
    webzine_domains: tuple[str, ...] = ("ign.com", "pcgamer.com", "gamespot.com", "rockpapershotgun.com")
    blog_domains: tuple[str, ...] = ("medium.com", "substack.com", "wordpress.com", "blogspot.com")

    # 성공 라벨 기준
    success_review_threshold: int = 500
    success_positive_rate_threshold: float = 0.80

    # 학습/평가 기준
    random_state: int = 42
    test_size_large_sample: float = 0.30
    test_size_small_sample: float = 0.40
    small_sample_cutoff: int = 20

    # 모델 후보 수와 주요 하이퍼파라미터
    use_logistic_regression: bool = True
    use_random_forest: bool = True
    logistic_max_iter: int = 1000
    random_forest_n_estimators: int = 300
    random_forest_max_depth: int = 6
    random_forest_min_samples_leaf: int = 2


SETTINGS = ProjectSettings()


def settings_table(settings: ProjectSettings = SETTINGS) -> list[tuple[str, object]]:
    return [(field.name, getattr(settings, field.name)) for field in fields(settings)]


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    data_raw: Path
    data_interim: Path
    data_processed: Path
    reports: Path
    figures: Path
    models: Path
    docs: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectPaths":
        paths = cls(
            root=root,
            data_raw=root / "data" / "raw",
            data_interim=root / "data" / "interim",
            data_processed=root / "data" / "processed",
            reports=root / "reports",
            figures=root / "reports" / "figures",
            models=root / "models",
            docs=root / "docs",
        )
        for path in paths.__dict__.values():
            if isinstance(path, Path) and path != root:
                path.mkdir(parents=True, exist_ok=True)
        return paths
