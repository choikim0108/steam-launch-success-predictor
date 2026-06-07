from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from steam_success.pipeline_90d import run


def _row(index: int, success: bool) -> dict[str, object]:
    reviews = 700 if success else 120
    positive_rate = 0.9 if success else 0.5
    return {
        "appid": 1000 + index,
        "name": f"90d Game {index}",
        "type": "game",
        "detail_success": True,
        "release_date_text": "Jan 10, 2025",
        "release_date": "2025-01-10",
        "label_eligible_90d": True,
        "success_90d": success,
        "reviews_30d": reviews // 2,
        "reviews_90d": reviews,
        "positive_rate_90d": positive_rate,
        "price_final_usd": 19.99 + index,
        "is_free": False,
        "required_age": 0,
        "discount_percent": 0,
        "supported_languages_raw": "English, Korean",
        "genres": "Action" if index < 6 else "Puzzle",
        "steam_tags": "Action, Indie" if index < 6 else "Puzzle, Indie",
        "categories": "Single-player, Steam Achievements, Full controller support",
        "platform_windows": True,
        "platform_mac": index % 2 == 0,
        "platform_linux": False,
        "coming_soon": False,
    }


class Pipeline90dTests(unittest.TestCase):
    def test_run_generates_separate_90d_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data" / "interim").mkdir(parents=True)
            release_window = pd.DataFrame({"appid": list(range(1000, 1020))})
            release_window.to_csv(root / "data" / "interim" / "search_release_window_appids.csv", index=False)
            rows = [_row(index, index < 6) for index in range(12)]
            pd.DataFrame(rows).to_csv(root / "data" / "interim" / "game_review_windows_2025_2026.csv", index=False)

            reports_dir = run(root)

            self.assertEqual(reports_dir, root / "reports" / "90d")
            self.assertTrue((root / "data" / "processed" / "modeling_dataset_90d.csv").exists())
            self.assertTrue((reports_dir / "predictions.csv").exists())
            self.assertFalse((root / "reports" / "predictions_90d.csv").exists())
            self.assertTrue((root / "models" / "steam_success_90d_model.joblib").exists())
            run_summary = (reports_dir / "RUN_SUMMARY.md").read_text(encoding="utf-8")
            self.assertIn("reports/90d/CONCLUSIONS.md", run_summary)
            self.assertIn("reports/90d/figures/", run_summary)
            self.assertNotIn("reports/CONCLUSIONS.md", run_summary)
            market_html = (reports_dir / "market_insight_site.html").read_text(encoding="utf-8")
            interactive_html = (reports_dir / "interactive_report.html").read_text(encoding="utf-8")
            self.assertIn("모집단 coverage", market_html)
            self.assertIn("review_count_90d", market_html)
            self.assertIn("그래서 성공할 것으로 예측되는 게임은 뭔가?", interactive_html)


if __name__ == "__main__":
    unittest.main()
