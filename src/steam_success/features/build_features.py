from __future__ import annotations

import pandas as pd

FEATURE_COLUMNS = [
    "price_final_usd",
    "is_free",
    "required_age",
    "discount_percent",
    "metacritic_score",
    "supported_language_count",
    "genre_count",
    "category_count",
    "has_multiplayer",
    "has_singleplayer",
    "supports_achievements",
    "supports_controller",
    "platform_windows",
    "platform_mac",
    "platform_linux",
]


def make_xy(dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    missing = [col for col in FEATURE_COLUMNS + ["success"] if col not in dataset.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    x = dataset[FEATURE_COLUMNS].copy()
    for col in x.columns:
        if x[col].dtype == bool:
            x[col] = x[col].astype(int)
    x = x.fillna(0)
    y = dataset["success"].astype(int)
    return x, y
