from __future__ import annotations

import unittest

import pandas as pd

from steam_success.config import SETTINGS
from steam_success.review_analysis import _keywords, high_success_genres


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
