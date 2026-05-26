from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def make_charts(dataset: pd.DataFrame, feature_importance: pd.DataFrame, figures_dir: Path) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    plt.figure(figsize=(7, 4))
    dataset["success"].map({0: "not_success", 1: "success"}).value_counts().plot(kind="bar", color=["#6b7280", "#2563eb"])
    plt.title("Success label distribution")
    plt.ylabel("games")
    plt.tight_layout()
    path = figures_dir / "label_distribution.png"
    plt.savefig(path, dpi=150)
    plt.close()
    paths.append(path)

    plt.figure(figsize=(7, 4))
    plt.scatter(dataset["total_reviews"], dataset["positive_rate"], c=dataset["success"], cmap="coolwarm", alpha=0.75)
    plt.xscale("symlog")
    plt.xlabel("total reviews (symlog)")
    plt.ylabel("positive rate")
    plt.title("Success proxy: reviews and positive rate")
    plt.tight_layout()
    path = figures_dir / "reviews_vs_positive_rate.png"
    plt.savefig(path, dpi=150)
    plt.close()
    paths.append(path)

    top = feature_importance.head(10).sort_values("importance")
    plt.figure(figsize=(8, 5))
    plt.barh(top["feature"], top["importance"], color="#16a34a")
    plt.title("Top model feature importance")
    plt.tight_layout()
    path = figures_dir / "feature_importance.png"
    plt.savefig(path, dpi=150)
    plt.close()
    paths.append(path)
    return paths
