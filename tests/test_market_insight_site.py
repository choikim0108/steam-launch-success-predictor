from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from typing import cast

import pandas as pd

from steam_success.features.build_features import PREDICTION_FEATURE_COLUMNS
from steam_success.market_insight import build_market_insight_payload
from steam_success.market_report import write_market_insight_site


def sample_dataset() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "appid": 10,
            "name": "Successful Action RPG",
            "genres": "Action, RPG",
            "steam_tags": "Action, RPG, Multiplayer, Free to Play",
            "categories": "Single-player, Full controller support, Steam Achievements",
            "price_final_usd": 19.99,
            "supported_language_count": 12,
            "platform_windows": True,
            "platform_mac": False,
            "platform_linux": False,
            "header_image": "https://cdn.cloudflare.steamstatic.com/steam/apps/10/header.jpg",
            "has_multiplayer": False,
            "has_singleplayer": True,
            "supports_controller": True,
            "supports_achievements": True,
            "total_reviews": 1200,
            "positive_rate": 0.91,
            "success": 1,
            "predicted_success_probability": 0.82,
            "external_attention_score": 18,
            "webzine_mentions": 5,
            "youtube_mentions": 8,
            "blog_mentions": 5,
        },
        {
            "appid": 20,
            "name": "Risky Action RPG",
            "genres": "Action, RPG",
            "steam_tags": "RPG, Cute",
            "categories": "Single-player",
            "price_final_usd": 29.99,
            "supported_language_count": 4,
            "platform_windows": True,
            "platform_mac": False,
            "platform_linux": False,
            "header_image": "https://cdn.cloudflare.steamstatic.com/steam/apps/20/header.jpg",
            "has_multiplayer": False,
            "has_singleplayer": True,
            "supports_controller": False,
            "supports_achievements": False,
            "total_reviews": 140,
            "positive_rate": 0.62,
            "success": 0,
            "predicted_success_probability": 0.24,
            "external_attention_score": 0,
            "webzine_mentions": 0,
            "youtube_mentions": 0,
            "blog_mentions": 0,
        },
        {
            "appid": 30,
            "name": "Puzzle Builder",
            "genres": "Puzzle, Simulation",
            "steam_tags": "Puzzle, Cute",
            "categories": "Single-player, Steam Achievements",
            "price_final_usd": 9.99,
            "supported_language_count": 8,
            "platform_windows": True,
            "platform_mac": True,
            "platform_linux": False,
            "header_image": "https://cdn.cloudflare.steamstatic.com/steam/apps/30/header.jpg",
            "has_multiplayer": False,
            "has_singleplayer": True,
            "supports_controller": False,
            "supports_achievements": True,
            "total_reviews": 360,
            "positive_rate": 0.86,
            "success": 1,
            "predicted_success_probability": 0.71,
            "external_attention_score": 3,
            "webzine_mentions": 1,
            "youtube_mentions": 2,
            "blog_mentions": 0,
        },
        {
            "appid": 40,
            "name": "Quoted <Builder>",
            "genres": "Builder \"Deluxe\", Strategy <Test>",
            "steam_tags": "Strategy <Test>, Multiplayer",
            "categories": "Multi-player, Co-op",
            "price_final_usd": 39.99,
            "supported_language_count": 3,
            "platform_windows": True,
            "platform_mac": True,
            "platform_linux": True,
            "header_image": "https://cdn.cloudflare.steamstatic.com/steam/apps/40/header.jpg",
            "has_multiplayer": True,
            "has_singleplayer": False,
            "supports_controller": False,
            "supports_achievements": False,
            "total_reviews": 80,
            "positive_rate": 0.58,
            "success": 0,
            "predicted_success_probability": 0.18,
            "external_attention_score": 0,
            "webzine_mentions": 0,
            "youtube_mentions": 0,
            "blog_mentions": 0,
        },
    ])


def sample_feature_importance() -> pd.DataFrame:
    return pd.DataFrame([
        {"feature": "price_final_usd", "importance": 0.31},
        {"feature": "supported_language_count", "importance": 0.22},
    ])


class MarketInsightSiteTests(unittest.TestCase):
    def test_market_payload_happy_path(self) -> None:
        payload = build_market_insight_payload(sample_dataset(), pd.DataFrame(), sample_feature_importance())
        project = cast(dict[str, object], payload["project"])
        summary = cast(dict[str, object], payload["summary"])
        developer_inputs = cast(dict[str, object], payload["developer_inputs"])
        similar_games = cast(dict[str, object], payload["similar_games"])
        recommendations = cast(dict[str, object], payload["recommendations"])
        developer_guidance = cast(dict[str, object], payload["developer_guidance"])
        feature_importance = cast(list[dict[str, object]], payload["feature_importance"])
        games = cast(list[dict[str, object]], payload["games"])

        self.assertEqual(project["mode"], "static_html")
        self.assertGreater(int(str(summary["game_count"])), 0)
        self.assertTrue(developer_inputs["genres"])
        self.assertTrue(developer_inputs["tags"])
        input_genres = cast(list[str], developer_inputs["genres"])
        input_tags = cast(list[str], developer_inputs["tags"])
        self.assertNotIn("Free To Play", input_genres)
        self.assertNotIn("Early Access", input_genres)
        self.assertNotIn("Action", input_tags)
        self.assertNotIn("RPG", input_tags)
        self.assertIn("Free to Play", input_tags)
        self.assertTrue(payload["market_trends"])
        self.assertTrue(games)
        self.assertIn("outcome_label", games[0])
        self.assertIn("model_opinion", games[0])
        self.assertIn("header_image", games[0])
        self.assertIn("platform_count", games[0])
        self.assertIn("review_growth_label", games[0])
        self.assertEqual(feature_importance[0]["feature"], "price_final_usd")
        self.assertTrue(similar_games["success_examples"])
        self.assertTrue(recommendations["development_cautions"])
        self.assertEqual(developer_guidance["name"], "기획 인사이트 추천 엔진")
        self.assertTrue(developer_guidance["cards"])
        self.assertTrue(developer_guidance["checklist"])

    def test_market_payload_filters_noisy_review_keywords(self) -> None:
        topics = pd.DataFrame([
            {"review_sentiment": "negative", "top_terms": "ayy, optimization, es, nie, bug, aaa"},
            {"review_sentiment": "positive", "top_terms": "fun, ayy, replay"},
        ])

        payload = build_market_insight_payload(sample_dataset(), topics, sample_feature_importance())
        recommendations = cast(dict[str, object], payload["recommendations"])

        self.assertEqual(recommendations["development_cautions"], ["optimization", "bug"])
        self.assertEqual(recommendations["positioning_strengths"], ["fun", "replay"])

    def test_external_availability_disabled_when_data_missing(self) -> None:
        data = sample_dataset()
        data[["webzine_mentions", "youtube_mentions", "blog_mentions", "external_attention_score"]] = 0

        payload = build_market_insight_payload(data, pd.DataFrame())
        external_data = cast(dict[str, object], payload["external_data"])
        webzine = cast(dict[str, object], external_data["webzine"])
        critic_score = cast(dict[str, object], external_data["critic_score"])

        self.assertFalse(webzine["enabled"])
        self.assertIn("데이터 부족", str(webzine["reason"]))
        self.assertFalse(critic_score["enabled"])
        self.assertIn("평점", str(critic_score["reason"]))

    def test_prediction_feature_columns_exclude_future_outcomes(self) -> None:
        forbidden = {
            "total_reviews",
            "positive_rate",
            "review_count_30d",
            "review_count_90d",
            "positive_rate_30d",
            "positive_rate_90d",
            "external_attention_score",
            "webzine_mentions",
            "youtube_mentions",
            "blog_mentions",
            "metacritic_score",
        }

        self.assertTrue(PREDICTION_FEATURE_COLUMNS)
        self.assertFalse(forbidden.intersection(PREDICTION_FEATURE_COLUMNS))

    def test_write_market_insight_site_creates_static_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir)
            output = write_market_insight_site(reports_dir, sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn("Steam 시장 트렌드", html)
        self.assertIn("장르", html)
        self.assertIn("메인 장르/세부 장르", html)
        self.assertIn("가격", html)
        self.assertIn("https://store.steampowered.com/app/10/", html)
        self.assertIn("데이터 부족", html)

        match = re.search(r'<script id="market-data" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(match)
        if match is None:
            self.fail("market data payload script is missing")
        payload = json.loads(match.group(1))
        project = cast(dict[str, object], payload["project"])
        self.assertEqual(project["mode"], "static_html")
        games = cast(list[dict[str, object]], payload["games"])
        quoted = next(game for game in games if str(game["appid"]) == "40")
        self.assertEqual(quoted["name"], "Quoted <Builder>")
        self.assertIn("Strategy <Test>", str(quoted["steam_tags"]))
        self.assertNotIn("</script>", match.group(1).lower())

    def test_static_html_renders_detailed_controls_and_escapes_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame())
            html = output.read_text(encoding="utf-8")

        self.assertIn("platform_windows", html)
        self.assertIn("platform_mac", html)
        self.assertIn("platform_linux", html)
        self.assertIn("has_multiplayer", html)
        self.assertIn("supports_controller", html)
        self.assertIn("supports_achievements", html)
        self.assertIn("document.createElement", html)
        self.assertNotIn('value="Builder "Deluxe"', html)
        self.assertIn("기획 입력 반영", html)
        self.assertIn("기획 인사이트 추천 엔진", html)
        self.assertIn("renderGuidance", html)
        self.assertIn("출시 전 체크리스트", html)

    def test_static_html_contains_game_list_modal_and_impact_chips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame())
            html = output.read_text(encoding="utf-8")

        self.assertIn("selectedGames", html)
        self.assertIn("tagComboRecommendations", html)
        self.assertIn("선택 장르 기준 성공확률 높은 태그 조합", html)
        self.assertIn("tagComboCandidates", html)
        self.assertIn("renderTagComboRecommendations", html)
        self.assertIn("gameModal", html)
        self.assertIn("openGameDetail", html)
        self.assertIn("renderImpactChips", html)
        self.assertIn("data-impact-disabled", html)
        self.assertIn("feature importance", html)
        self.assertIn("리뷰 성장률", html)

    def test_static_html_contains_tabs_balanced_cards_images_and_explanations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn("tab-button", html)
        self.assertIn("tab-panel", html)
        self.assertIn("선택 조건 기반 참고 게임", html)
        self.assertIn("successReferenceGames", html)
        self.assertIn("riskReferenceGames", html)
        self.assertIn("header_image", html)
        self.assertIn("createGameImage", html)
        self.assertIn("importance_description", html)
        self.assertIn("featureHelpText", html)
        self.assertIn("선택 전에는 전체 시장 평균", html)

    def test_static_html_documents_criteria_trends_and_blank_planning_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn("성공/중박/실패 기준", html)
        self.assertIn("성공: 65% 이상", html)
        self.assertIn("trend-up", html)
        self.assertIn("trend-flat", html)
        self.assertIn("trend-down", html)
        self.assertIn("↗", html)
        self.assertIn("→", html)
        self.assertIn("↘", html)
        self.assertIn("numeric(target, 'price', '가격', '')", html)
        self.assertIn("numeric(target, 'languages', '언어 수', '')", html)
        self.assertIn("numeric(target, 'month', '출시월', '', '1', '12')", html)
        self.assertIn("이 탭의 쓰임", html)
        self.assertIn("개발자 시나리오", html)
        self.assertIn("시장 스냅샷", html)
        self.assertIn("내 게임 진단", html)
        self.assertIn("성공 레퍼런스", html)
        self.assertIn("판단 기준", html)
        self.assertIn("tab-shell", html)

    def test_static_html_handles_nan_and_preserves_special_characters(self) -> None:
        data = sample_dataset()
        data["external_attention_score"] = data["external_attention_score"].astype(float)
        data["success"] = data["success"].astype(float)
        data.loc[0, "name"] = "A & B </script> <Test>"
        data.loc[0, "total_reviews"] = float("nan")
        data.loc[0, "predicted_success_probability"] = float("nan")
        data.loc[1, "positive_rate"] = float("inf")
        data.loc[1, "success"] = float("inf")
        data.loc[2, "external_attention_score"] = float("-inf")
        data.loc[3, "metacritic_score"] = float("inf")

        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), data, pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        match = re.search(r'<script id="market-data" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(match)
        if match is None:
            self.fail("market data payload script is missing")
        payload = json.loads(match.group(1))
        games = cast(list[dict[str, object]], payload["games"])
        self.assertEqual(games[-1]["name"], "A & B </script> <Test>")
        self.assertEqual(games[-1]["total_reviews"], 0)
        self.assertEqual(games[-1]["predicted_success_probability"], 0.0)


if __name__ == "__main__":
    unittest.main()
