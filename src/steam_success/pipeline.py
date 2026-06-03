from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from steam_success.collect.external_web import collect_external_web_signals
from steam_success.collect.steam import collect_all, fetch_review_texts
from steam_success.config import ProjectPaths, SETTINGS
from steam_success.models.train import train_and_evaluate
from steam_success.market_report import write_market_insight_site
from steam_success.preprocess.dataset import build_modeling_dataset
from steam_success.reporting import summarize_pdf, write_architecture_doc, write_assumptions_doc, write_manual_doc, write_run_summary, write_workspace_docs_index
from steam_success.review_analysis import analyze_review_topics, select_review_games
from steam_success.web_report import write_interactive_report
from steam_success.visualize.charts import make_charts


def run(root: Path, max_apps: int | None = None) -> None:
    paths = ProjectPaths.from_root(root)
    collected = collect_all(paths, settings=SETTINGS, max_apps=max_apps)
    dataset = build_modeling_dataset(collected["search"], collected["details"], collected["reviews"], settings=SETTINGS)
    if len(dataset) < 20:
        raise RuntimeError(f"Only {len(dataset)} valid games collected; increase --max-apps.")
    external_signals = collect_external_web_signals(dataset, paths.data_raw, settings=SETTINGS)
    dataset = dataset.merge(external_signals, on="appid", how="left")
    for col in ["youtube_mentions", "webzine_mentions", "blog_mentions", "external_attention_score"]:
        dataset[col] = dataset[col].fillna(0).astype(int)
    dataset["external_signal_success"] = dataset["external_signal_success"].fillna(False).astype(bool)
    dataset.to_csv(paths.data_interim / "merged_games.csv", index=False)
    dataset.to_csv(paths.data_processed / "modeling_dataset.csv", index=False)
    result = train_and_evaluate(dataset, paths.models, paths.reports, settings=SETTINGS)
    predictions = pd.read_csv(paths.reports / "predictions.csv")[["appid", "predicted_success_probability"]]
    dataset = dataset.merge(predictions, on="appid", how="left")
    review_targets = select_review_games(dataset, settings=SETTINGS)
    review_texts = fetch_review_texts(review_targets["appid"].astype(int).tolist(), paths.data_raw, collected["config"], SETTINGS.review_texts_per_game)
    review_analysis = analyze_review_topics(dataset, review_texts, paths.reports)
    review_samples = pd.read_csv(paths.reports / "review_samples.csv") if (paths.reports / "review_samples.csv").exists() else pd.DataFrame()
    feature_importance = result.get("feature_importance")
    if not isinstance(feature_importance, pd.DataFrame):
        feature_importance = pd.read_csv(paths.reports / "feature_importance.csv")
    chart_paths = make_charts(dataset, feature_importance, paths.figures, review_analysis)
    summarize_pdf(root.parent / "1조 게임 (1).pdf", paths.docs / "PDF_REFERENCE_SUMMARY.md")
    write_architecture_doc(paths.docs)
    write_manual_doc(paths.docs)
    write_assumptions_doc(paths.docs, dataset, result)
    write_workspace_docs_index(root, paths.docs)
    write_run_summary(paths.reports, dataset, result, chart_paths)
    write_interactive_report(paths.reports, dataset)
    write_market_insight_site(paths.reports, dataset, pd.DataFrame(review_analysis.get("summary", [])), feature_importance, review_samples)
    print("Steam success prediction pipeline completed")
    success_count = len(dataset[dataset["success"] == 1])
    print(f"valid_games={len(dataset)} success={success_count} best_model={result['best_model']}")
    print(f"reports={paths.reports}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Steam data and train a launch success prediction model.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--max-apps", type=int, default=None, help="Override SETTINGS.max_apps for one run")
    args = parser.parse_args()
    run(args.root.resolve(), args.max_apps)


if __name__ == "__main__":
    main()
