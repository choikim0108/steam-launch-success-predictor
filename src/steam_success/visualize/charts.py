from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def make_charts(dataset: pd.DataFrame, feature_importance: pd.DataFrame, figures_dir: Path, review_analysis: dict[str, object] | None = None) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    plt.figure(figsize=(7, 4))
    dataset["success"].map(lambda value: "success" if int(value) == 1 else "not_success").value_counts().plot(kind="bar", color=["#6b7280", "#2563eb"])
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

    plt.figure(figsize=(10, 3))
    steps = ["Steam\nsearch", "Store/API\nmerge", "Success\nmodel", "Top genre\nreviews", "Topic\nconclusion"]
    xs = range(len(steps))
    plt.scatter(xs, [1] * len(steps), s=900, color="#2563eb")
    for idx, step in enumerate(steps):
        plt.text(idx, 1, step, color="white", ha="center", va="center", fontsize=9, weight="bold")
        if idx < len(steps) - 1:
            plt.annotate("", xy=(idx + 0.72, 1), xytext=(idx + 0.28, 1), arrowprops={"arrowstyle": "->", "color": "#111827", "lw": 2})
    plt.axis("off")
    plt.title("Analysis workflow")
    plt.tight_layout()
    path = figures_dir / "analysis_workflow.png"
    plt.savefig(path, dpi=150)
    plt.close()
    paths.append(path)

    if review_analysis:
        summary = pd.DataFrame(review_analysis.get("summary") or [])
        if not summary.empty:
            pivot = summary.pivot_table(index="genre", columns=["game_success", "review_sentiment"], values="review_count", aggfunc="sum", fill_value=0)
            pivot.plot(kind="bar", figsize=(9, 5))
            plt.title("Review text counts by top genre")
            plt.ylabel("reviews")
            plt.xticks(rotation=25, ha="right")
            plt.tight_layout()
            path = figures_dir / "review_topic_counts.png"
            plt.savefig(path, dpi=150)
            plt.close()
            paths.append(path)
    return paths
