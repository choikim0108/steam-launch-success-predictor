from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from steam_success.collect.steam import CrawlConfig, fetch_appdetails, fetch_review_summaries


class FailingSession:
    headers: dict[str, str]

    def __init__(self) -> None:
        self.headers = {}

    def get(self, *_args: object, **_kwargs: object) -> object:
        raise RuntimeError("network disabled")


class SteamCollectionTests(unittest.TestCase):
    def test_fetch_appdetails_uses_cached_json_and_keeps_header_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = Path(temp_dir)
            (raw_dir / "appdetails_10.json").write_text(json.dumps({
                "10": {
                    "success": True,
                    "data": {
                        "name": "Cached Game",
                        "type": "game",
                        "is_free": False,
                        "release_date": {"date": "Jan 1, 2025", "coming_soon": False},
                        "header_image": "https://cdn.cloudflare.steamstatic.com/steam/apps/10/header.jpg",
                        "platforms": {"windows": True, "mac": False, "linux": False},
                    },
                }
            }), encoding="utf-8")

            with patch("steam_success.collect.steam.requests.Session", FailingSession):
                rows = fetch_appdetails([10], raw_dir, CrawlConfig(1, 1, 0, "US", "english"))

        self.assertTrue(bool(rows.loc[0, "detail_success"]))
        self.assertEqual(rows.loc[0, "name"], "Cached Game")
        self.assertIn("header.jpg", str(rows.loc[0, "header_image"]))

    def test_fetch_review_summaries_uses_cached_json_when_network_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = Path(temp_dir)
            (raw_dir / "review_summary_10.json").write_text(json.dumps({
                "success": 1,
                "query_summary": {
                    "review_score": 8,
                    "review_score_desc": "Very Positive",
                    "total_reviews": 100,
                    "total_positive": 90,
                    "total_negative": 10,
                },
            }), encoding="utf-8")

            with patch("steam_success.collect.steam.requests.Session", FailingSession):
                rows = fetch_review_summaries([10], raw_dir, CrawlConfig(1, 1, 0, "US", "english"))

        self.assertTrue(bool(rows.loc[0, "review_success"]))
        self.assertEqual(int(rows.loc[0, "total_reviews"]), 100)
        self.assertEqual(float(rows.loc[0, "positive_rate"]), 0.9)


if __name__ == "__main__":
    unittest.main()
