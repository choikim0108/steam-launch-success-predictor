from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from steam_success.reporting import build_criteria_tables
from steam_success.web_report import write_interactive_report


def sample_dataset() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "appid": 10,
            "name": "Reference Success",
            "genres": "Action, Indie",
            "steam_tags": "Action, Combat, Early Access",
            "categories": "Single-player, Steam Achievements",
            "is_free": False,
            "coming_soon": False,
            "price_final_usd": 19.99,
            "supported_language_count": 8,
            "platform_windows": True,
            "platform_mac": False,
            "platform_linux": False,
            "supports_controller": True,
            "supports_achievements": True,
            "has_multiplayer": False,
            "total_reviews": 900,
            "positive_rate": 0.91,
            "success": 1,
            "predicted_success_probability": 0.82,
            "webzine_mentions": 2,
            "webzine_source_count": 2,
            "external_attention_score": 4,
        },
        {
            "appid": 20,
            "name": "Reference Risk",
            "genres": "Action",
            "steam_tags": "Action, Bugs",
            "categories": "Single-player",
            "is_free": False,
            "coming_soon": False,
            "price_final_usd": 29.99,
            "supported_language_count": 2,
            "platform_windows": True,
            "platform_mac": False,
            "platform_linux": False,
            "supports_controller": False,
            "supports_achievements": False,
            "has_multiplayer": False,
            "total_reviews": 120,
            "positive_rate": 0.52,
            "success": 0,
            "predicted_success_probability": 0.22,
            "webzine_mentions": 0,
            "webzine_source_count": 2,
            "external_attention_score": 0,
        },
    ])


class WebReportTests(unittest.TestCase):
    def test_criteria_tables_exclude_missing_genre_values(self) -> None:
        data = pd.concat([sample_dataset(), sample_dataset()], ignore_index=True)
        data.loc[[1, 2, 3], "genres"] = float("nan")

        tables = build_criteria_tables(data)
        genres = tables["genre"]["criteria_value"].astype(str).str.lower().tolist()

        self.assertNotIn("nan", genres)

    def test_interactive_report_reads_criteria_from_given_reports_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir)
            pd.DataFrame([{"model": "RandomForest", "f1": 0.8, "recall": 0.7, "accuracy": 0.75}]).to_csv(reports_dir / "model_metrics.csv", index=False)
            pd.DataFrame([{"appid": 10, "name": "Reference Success", "success": 1, "total_reviews": 900, "positive_rate": 0.91, "predicted_success_probability": 0.82}]).to_csv(reports_dir / "predictions.csv", index=False)
            pd.DataFrame([{"criteria_value": "Temp Genre", "success_rate": 0.75, "success_count": 3, "game_count": 4}]).to_csv(reports_dir / "criteria_genre.csv", index=False)
            pd.DataFrame([{"criteria_value": "Temp Price", "success_rate": 0.5, "success_count": 1, "game_count": 2}]).to_csv(reports_dir / "criteria_price_band.csv", index=False)
            pd.DataFrame([{"criteria_value": "Temp External", "success_rate": 0.25, "success_count": 1, "game_count": 4}]).to_csv(reports_dir / "criteria_external_attention.csv", index=False)

            write_interactive_report(reports_dir, sample_dataset())
            html = (reports_dir / "interactive_report.html").read_text(encoding="utf-8")

        self.assertIn("상위 장르 경향은 Temp Genre", html)

    def test_interactive_report_includes_semantic_external_and_reference_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir)
            pd.DataFrame([{"model": "RandomForest", "f1": 0.8, "recall": 0.7, "accuracy": 0.75}]).to_csv(reports_dir / "model_metrics.csv", index=False)
            pd.DataFrame([{"appid": 10, "name": "Reference Success", "success": 1, "total_reviews": 900, "positive_rate": 0.91, "predicted_success_probability": 0.82}]).to_csv(reports_dir / "predictions.csv", index=False)
            pd.DataFrame([{"criteria_value": "Action", "success_rate": 0.5, "success_count": 1, "game_count": 2}]).to_csv(reports_dir / "criteria_genre.csv", index=False)
            pd.DataFrame([{"genre": "Action", "game_success": "success", "review_sentiment": "positive", "review_count": 1, "top_terms": "combat"}]).to_csv(reports_dir / "review_topic_summary.csv", index=False)
            pd.DataFrame([
                {"appid": 10, "name": "Reference Success", "matched_genres": "Action", "success": 1, "voted_up": True, "playtime_hours": 3.0, "review_text": "combat gameplay replayability controller support"},
                {"appid": 20, "name": "Reference Risk", "matched_genres": "Action", "success": 0, "voted_up": False, "playtime_hours": 1.0, "review_text": "performance bugs crash stutter"},
            ]).to_csv(reports_dir / "review_samples.csv", index=False)

            write_interactive_report(reports_dir, sample_dataset())
            html = (reports_dir / "interactive_report.html").read_text(encoding="utf-8")

        self.assertIn("의미 모델·추천 신뢰도", html)
        self.assertIn("외부 데이터 상태", html)
        self.assertIn("성공/실패 참고 게임 선정 근거", html)
        self.assertIn("항목별 신뢰도", html)
        self.assertIn("선정 근거", html)
        self.assertIn("웹진 RSS/검색 경로 사용 가능", html)


if __name__ == "__main__":
    unittest.main()
