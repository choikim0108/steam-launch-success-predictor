from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from steam_success.preprocess.review_windows import build_review_windows, run


def _unix(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


class ReviewWindowsTests(unittest.TestCase):
    def test_builds_window_metrics_and_success_label(self) -> None:
        candidates = pd.DataFrame(
            [
                {
                    "appid": 1,
                    "release_date_text": "Jan 1, 2025",
                    "label_eligible_90d": True,
                }
            ]
        )
        histogram = pd.DataFrame(
            [
                {"appid": 1, "bucket_date_unix": _unix("2025-01-03"), "recommendations_up": 10, "recommendations_down": 2, "recommendations_total": 12},
                {"appid": 1, "bucket_date_unix": _unix("2025-01-20"), "recommendations_up": 20, "recommendations_down": 4, "recommendations_total": 24},
                {"appid": 1, "bucket_date_unix": _unix("2025-03-20"), "recommendations_up": 470, "recommendations_down": 20, "recommendations_total": 490},
                {"appid": 1, "bucket_date_unix": _unix("2025-04-20"), "recommendations_up": 999, "recommendations_down": 1, "recommendations_total": 1000},
            ]
        )

        result = build_review_windows(candidates, histogram)
        row = result.iloc[0]

        self.assertEqual(row["reviews_7d"], 12)
        self.assertEqual(row["reviews_30d"], 36)
        self.assertEqual(row["reviews_90d"], 526)
        self.assertAlmostEqual(row["positive_rate_90d"], 500 / 526)
        self.assertTrue(row["success_90d"])

    def test_non_eligible_game_cannot_be_success_label(self) -> None:
        candidates = pd.DataFrame(
            [
                {
                    "appid": 2,
                    "release_date_text": "May 1, 2026",
                    "label_eligible_90d": False,
                }
            ]
        )
        histogram = pd.DataFrame(
            [
                {"appid": 2, "bucket_date_unix": _unix("2026-05-07"), "recommendations_up": 900, "recommendations_down": 10, "recommendations_total": 910},
            ]
        )

        result = build_review_windows(candidates, histogram)

        self.assertEqual(result.iloc[0]["reviews_90d"], 910)
        self.assertFalse(result.iloc[0]["success_90d"])

    def test_run_fails_when_histogram_csv_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidates_dir = root / "data" / "interim"
            candidates_dir.mkdir(parents=True)
            pd.DataFrame([{"appid": 1, "release_date_text": "Jan 1, 2025", "label_eligible_90d": True}]).to_csv(candidates_dir / "game_candidates_2025_2026.csv", index=False)

            with self.assertRaises(FileNotFoundError):
                run(root, None, None, "game_review_windows_2025_2026.csv")


if __name__ == "__main__":
    unittest.main()
