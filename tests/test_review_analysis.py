from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from steam_success.config import SETTINGS
from steam_success.review_analysis import _keywords, analyze_review_topics, append_review_samples, high_success_genres, select_reference_review_games


class ReviewAnalysisTests(unittest.TestCase):
    def test_default_review_text_sampling_is_large_enough_for_report_evidence(self) -> None:
        self.assertEqual(SETTINGS.review_text_sample_size, 40)
        self.assertEqual(SETTINGS.review_texts_per_game, 100)

    def test_high_success_genres_excludes_strategy_and_missing_terms(self) -> None:
        dataset = pd.DataFrame([
            {"genres": "Free To Play, Indie", "success": 1, "predicted_success_probability": 0.9},
            {"genres": "Free To Play, Indie", "success": 1, "predicted_success_probability": 0.85},
            {"genres": "Free To Play, Indie", "success": 1, "predicted_success_probability": 0.82},
            {"genres": "nan, Early Access", "success": 1, "predicted_success_probability": 0.8},
            {"genres": "Action", "success": 1, "predicted_success_probability": 0.7},
            {"genres": "Action", "success": 0, "predicted_success_probability": 0.4},
            {"genres": "Action", "success": 1, "predicted_success_probability": 0.6},
        ])

        genres = high_success_genres(dataset, limit=3)

        self.assertEqual(genres, ["Action"])

    def test_select_reference_review_games_targets_success_and_risk_examples(self) -> None:
        data = pd.DataFrame([
            {"appid": 1, "name": "Top Success", "success": 1, "predicted_success_probability": 0.91, "total_reviews": 1000},
            {"appid": 2, "name": "Mid Success", "success": 1, "predicted_success_probability": 0.72, "total_reviews": 500},
            {"appid": 3, "name": "Weak Risk", "success": 0, "predicted_success_probability": 0.10, "total_reviews": 20},
            {"appid": 4, "name": "Less Weak Risk", "success": 0, "predicted_success_probability": 0.25, "total_reviews": 40},
        ])

        selected = select_reference_review_games(data, limit_per_group=1)

        self.assertEqual(selected["appid"].tolist(), [1, 3])
        self.assertEqual(selected["reference_group"].tolist(), ["success", "risk"])

    def test_append_review_samples_dedupes_by_appid_and_review_id(self) -> None:
        existing = pd.DataFrame([
            {"appid": 10, "review_id": "a", "review_text": "old text", "voted_up": True},
            {"appid": 10, "review_id": "b", "review_text": "kept text", "voted_up": False},
        ])
        new = pd.DataFrame([
            {"appid": 10, "review_id": "a", "review_text": "new text", "voted_up": True},
            {"appid": 20, "review_id": "c", "review_text": "fresh text", "voted_up": True},
        ])

        combined = append_review_samples(existing, new)

        self.assertEqual(len(combined), 3)
        self.assertEqual(combined[combined["review_id"] == "a"].iloc[0]["review_text"], "old text")
        self.assertIn("fresh text", combined["review_text"].tolist())

    def test_append_review_samples_preserves_legacy_rows_without_review_id(self) -> None:
        existing = pd.DataFrame([
            {"appid": 10, "review_text": "legacy one", "voted_up": True},
            {"appid": 10, "review_text": "legacy two", "voted_up": False},
        ])
        new = pd.DataFrame([
            {"appid": 10, "review_id": "fresh", "review_text": "fresh text", "voted_up": True},
        ])

        combined = append_review_samples(existing, new)

        self.assertEqual(len(combined), 3)
        self.assertIn("legacy one", combined["review_text"].tolist())
        self.assertIn("legacy two", combined["review_text"].tolist())
        self.assertIn("fresh text", combined["review_text"].tolist())

    def test_analyze_review_topics_persists_reference_only_review_rows(self) -> None:
        dataset = pd.DataFrame([
            {"appid": 1, "name": "Topic Target A", "genres": "Action", "success": 1, "predicted_success_probability": 0.8, "total_reviews": 100},
            {"appid": 2, "name": "Topic Target B", "genres": "Action", "success": 1, "predicted_success_probability": 0.7, "total_reviews": 100},
            {"appid": 3, "name": "Topic Target C", "genres": "Action", "success": 0, "predicted_success_probability": 0.2, "total_reviews": 100},
            {"appid": 4, "name": "Reference Only", "genres": "Puzzle", "success": 1, "predicted_success_probability": 0.95, "total_reviews": 1000},
        ])
        reviews = pd.DataFrame([
            {"appid": 4, "review_id": "ref", "name": "", "success": "", "voted_up": True, "playtime_hours": 3.0, "review_text": "combat gameplay replayability controller support"},
        ])

        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir)
            analyze_review_topics(dataset, reviews, reports_dir)
            samples = pd.read_csv(reports_dir / "review_samples.csv")
            topics = pd.read_csv(reports_dir / "review_topic_summary.csv")

        self.assertEqual(samples["appid"].tolist(), [4])
        self.assertEqual(samples["review_id"].tolist(), ["ref"])
        self.assertEqual(topics.columns.tolist(), ["genre", "game_success", "review_sentiment", "review_count", "top_terms"])

    def test_keywords_remove_generic_and_non_english_noise(self) -> None:
        texts = pd.Series([
            "game play just game play optimization stutter crash bug",
            "que la le game just controller support replayability",
            "great game but balance pacing progression matters",
        ])

        keywords = _keywords(texts)
        terms = [term.strip() for term in keywords.split(",")]

        self.assertNotIn("game", terms)
        self.assertNotIn("play", terms)
        self.assertNotIn("just", terms)
        self.assertNotIn("que", terms)
        self.assertNotIn("this", terms)
        self.assertNotIn("that", terms)
        self.assertNotIn("with", terms)
        self.assertIn("optimization", keywords)
        self.assertIn("controller", keywords)

    def test_keywords_returns_data_missing_when_only_stop_words_remain(self) -> None:
        keywords = _keywords(pd.Series(["game play just like good great", "que la le des pour jogo"]))

        self.assertEqual(keywords, "데이터 부족")


if __name__ == "__main__":
    unittest.main()
