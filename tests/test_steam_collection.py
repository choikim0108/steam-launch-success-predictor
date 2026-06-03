from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from steam_success.collect.steam import CrawlConfig, fetch_appdetails, fetch_review_summaries, fetch_review_texts


class FailingSession:
    headers: dict[str, str]

    def __init__(self) -> None:
        self.headers = {}

    def get(self, *_args: object, **_kwargs: object) -> object:
        raise RuntimeError("network disabled")


class FakeReviewResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class CursorReviewSession:
    headers: dict[str, str]
    calls: list[dict[str, object]] = []

    def __init__(self) -> None:
        self.headers = {}

    def get(self, _url: str, params: dict[str, object], **_kwargs: object) -> FakeReviewResponse:
        self.__class__.calls.append(dict(params))
        if len(self.__class__.calls) == 1:
            return FakeReviewResponse({
                "reviews": [
                    {"recommendationid": "1", "voted_up": True, "review": "first useful review body", "author": {"playtime_forever": 60}, "timestamp_created": 100},
                    {"recommendationid": "2", "voted_up": False, "review": "second useful review body", "author": {"playtime_forever": 120}, "timestamp_created": 200},
                ],
                "cursor": "next-cursor",
            })
        return FakeReviewResponse({
            "reviews": [
                {"recommendationid": "3", "voted_up": True, "review": "third useful review body", "author": {"playtime_forever": 180}, "timestamp_created": 300},
            ],
            "cursor": "done-cursor",
        })


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

    def test_fetch_review_texts_follows_cursor_until_per_game_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            CursorReviewSession.calls = []
            raw_dir = Path(temp_dir)
            with patch("steam_success.collect.steam.requests.Session", CursorReviewSession), patch("steam_success.collect.steam.time.sleep", return_value=None):
                rows = fetch_review_texts([10], raw_dir, CrawlConfig(1, 1, 0, "US", "english"), per_game=3)
            self.assertTrue((raw_dir / "review_texts" / "review_texts_10_page_1.json").exists())
            self.assertTrue((raw_dir / "review_texts" / "review_texts_10_page_2.json").exists())

        self.assertEqual(len(rows), 3)
        self.assertEqual(len(CursorReviewSession.calls), 2)
        self.assertEqual(CursorReviewSession.calls[0].get("cursor"), "*")
        self.assertEqual(CursorReviewSession.calls[1].get("cursor"), "next-cursor")


if __name__ == "__main__":
    unittest.main()
