from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from typing import cast

import pandas as pd

from steam_success.config import SETTINGS
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
            "categories": "Single-player, Full controller support, Steam Achievements, In-App Purchases",
            "is_free": True,
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
            "is_free": False,
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
            "is_free": False,
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
            "is_free": False,
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


def sample_review_samples() -> pd.DataFrame:
    return pd.DataFrame([
        {"appid": 10, "name": "Successful Action RPG", "matched_genres": "Action", "success": 1, "voted_up": True, "playtime_hours": 12.0, "review_text": "combat gameplay replayability controller support feels polished"},
        {"appid": 10, "name": "Successful Action RPG", "matched_genres": "Action", "success": 1, "voted_up": False, "playtime_hours": 2.0, "review_text": "performance stutter bugs crash during combat"},
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
        strategy_tags = cast(list[str], developer_inputs["strategy_tags"])
        self.assertNotIn("Free To Play", input_genres)
        self.assertNotIn("Early Access", input_genres)
        self.assertNotIn("Action", input_tags)
        self.assertNotIn("RPG", input_tags)
        self.assertNotIn("Free to Play", input_tags)
        self.assertIn("Free to Play", strategy_tags)
        self.assertTrue(payload["market_trends"])
        self.assertTrue(games)
        self.assertIn("outcome_label", games[0])
        self.assertIn("model_opinion", games[0])
        self.assertIn("header_image", games[0])
        self.assertIn("platform_count", games[0])
        self.assertIn("review_growth_label", games[0])
        self.assertIn("business_model", games[0])
        self.assertIn("lifecycle", games[0])
        self.assertIn("confidence", games[0])
        self.assertEqual(feature_importance[0]["feature"], "price_final_usd")
        self.assertTrue(similar_games["success_examples"])
        self.assertTrue(recommendations["development_cautions"])
        self.assertEqual(developer_guidance["name"], "조합 단위 집계 모델")
        self.assertTrue(developer_guidance["cards"])
        self.assertTrue(developer_guidance["checklist"])

    def test_developer_inputs_include_group_metadata_and_data_backed_checkboxes(self) -> None:
        data = sample_dataset()
        data["supports_cloud"] = [True, False, True, False]
        data["steam_tags"] = [", ".join(f"FeatureTag{index}" for index in range(18)), "RPG, Cute", "Puzzle, Cute", "Strategy <Test>, Multiplayer"]

        payload = build_market_insight_payload(data, pd.DataFrame(), sample_feature_importance())
        developer_inputs = cast(dict[str, object], payload["developer_inputs"])
        groups = cast(list[dict[str, object]], developer_inputs["input_groups"])
        group_keys = [str(group["key"]) for group in groups]
        checkbox_fields = cast(list[str], developer_inputs["checkbox_fields"])
        genre_group = next(group for group in groups if group["key"] == "genres")
        tag_group = next(group for group in groups if group["key"] == "tags")

        self.assertEqual(group_keys, ["genres", "strategy_tags", "tags", "checkbox_fields"])
        self.assertTrue(bool(genre_group["searchable"]))
        self.assertGreater(int(str(genre_group["initial_visible"])), 0)
        self.assertGreaterEqual(len(cast(list[str], genre_group["options"])), len(cast(list[str], developer_inputs["genres"])))
        self.assertTrue(bool(tag_group["show_more"]))
        self.assertIn("has_singleplayer", checkbox_fields)
        self.assertIn("is_free", checkbox_fields)
        self.assertIn("supports_cloud", checkbox_fields)
        self.assertNotIn("supports_vr", checkbox_fields)

    def test_developer_input_search_options_include_tags_beyond_visible_limit(self) -> None:
        rows = []
        for index in range(80):
            rows.append({
                "appid": 7000 + index,
                "name": f"Tag Game {index}",
                "genres": "Action",
                "steam_tags": f"SearchableTag{index:02d}",
                "categories": "Single-player",
                "success": 1 if index % 2 == 0 else 0,
                "predicted_success_probability": 0.7 if index % 2 == 0 else 0.3,
                "total_reviews": 100 + index,
                "positive_rate": 0.8,
            })

        payload = build_market_insight_payload(pd.DataFrame(rows), pd.DataFrame(), sample_feature_importance())
        summary = cast(dict[str, object], payload["summary"])
        developer_inputs = cast(dict[str, object], payload["developer_inputs"])
        groups = cast(list[dict[str, object]], developer_inputs["input_groups"])
        tag_group = next(group for group in groups if group["key"] == "tags")
        tag_options = cast(list[str], tag_group["options"])

        self.assertEqual(summary["analyzed_tag_count"], 80)
        self.assertIn("SearchableTag79", tag_options)
        self.assertGreater(len(tag_options), int(str(tag_group["initial_visible"])))

    def test_developer_input_search_options_include_genres_beyond_visible_limit(self) -> None:
        rows = []
        for index in range(80):
            rows.append({
                "appid": 8000 + index,
                "name": f"Genre Game {index}",
                "genres": f"SearchableGenre{index:02d}",
                "steam_tags": "SharedTag",
                "categories": "Single-player",
                "success": 1 if index % 2 == 0 else 0,
                "predicted_success_probability": 0.7 if index % 2 == 0 else 0.3,
                "total_reviews": 100 + index,
                "positive_rate": 0.8,
            })

        payload = build_market_insight_payload(pd.DataFrame(rows), pd.DataFrame(), sample_feature_importance())
        developer_inputs = cast(dict[str, object], payload["developer_inputs"])
        groups = cast(list[dict[str, object]], developer_inputs["input_groups"])
        genre_group = next(group for group in groups if group["key"] == "genres")
        genre_options = cast(list[str], genre_group["options"])

        self.assertIn("SearchableGenre79", genre_options)
        self.assertGreater(len(genre_options), int(str(genre_group["initial_visible"])))

    def test_market_payload_maps_review_window_columns_to_card_counts(self) -> None:
        data = sample_dataset()
        data["reviews_30d"] = [31, 0, 12, 4]
        data["reviews_90d"] = [91, 0, 42, 9]

        payload = build_market_insight_payload(data, pd.DataFrame(), sample_feature_importance())
        games = cast(list[dict[str, object]], payload["games"])
        game = next(row for row in games if row["appid"] == 10)

        self.assertEqual(game["review_count_30d"], 31)
        self.assertEqual(game["review_count_90d"], 91)
        self.assertEqual(game["review_growth_label"], "30일 31개 / 90일 91개")

    def test_market_payload_adds_semantic_model_and_review_reference_reasons(self) -> None:
        payload = build_market_insight_payload(sample_dataset(), pd.DataFrame(), sample_feature_importance(), sample_review_samples())
        summary = cast(dict[str, object], payload["summary"])
        semantic = cast(dict[str, object], payload["semantic_model"])
        games = cast(list[dict[str, object]], payload["games"])
        game = next(row for row in games if int(str(row["appid"])) == 10)
        evidence = cast(dict[str, object], game["review_evidence"])

        self.assertEqual(summary["analyzed_tag_count"], 7)
        self.assertTrue(semantic["business_models"])
        self.assertTrue(semantic["lifecycles"])
        self.assertTrue(semantic["production_contexts"])
        self.assertIn("confidence", semantic)
        self.assertEqual(game["business_model"], "Free to Play")
        self.assertEqual(game["lifecycle"], "Released")
        self.assertEqual(game["confidence"], "높음")
        profile = cast(dict[str, object], game["semantic_profile"])
        business = cast(dict[str, object], profile["business_model"])
        self.assertEqual(business["value"], "Free to Play")
        self.assertGreater(float(str(business["confidence"])), 0.9)
        self.assertIn("overall_confidence", profile)
        self.assertIn("confidence_band", profile)
        self.assertEqual(evidence["sample_count"], 2)
        self.assertIn("combat", str(evidence["positive_terms"]))
        self.assertIn("performance", str(evidence["negative_terms"]))
        self.assertIn("크롤링 리뷰 2개", str(game["reference_reason"]))

    def test_similar_games_keep_observed_references_without_review_body_split(self) -> None:
        data = sample_dataset()
        reviews = pd.DataFrame([
            {"appid": 10, "name": "Successful Action RPG", "matched_genres": "Action", "success": 1, "voted_up": True, "playtime_hours": 2.0, "review_text": f"combat gameplay replayability controller support {index}"}
            for index in range(5)
        ] + [
            {"appid": 20, "name": "Risky Action RPG", "matched_genres": "Action", "success": 0, "voted_up": False, "playtime_hours": 1.0, "review_text": "performance bugs crash stutter"}
        ])

        payload = build_market_insight_payload(data, pd.DataFrame(), sample_feature_importance(), reviews)
        similar_games = cast(dict[str, object], payload["similar_games"])
        success_examples = cast(list[dict[str, object]], similar_games["success_examples"])
        risk_examples = cast(list[dict[str, object]], similar_games["risk_examples"])

        self.assertIn(10, [game["appid"] for game in success_examples])
        self.assertIn(30, [game["appid"] for game in success_examples])
        self.assertIn(20, [game["appid"] for game in risk_examples])
        self.assertNotIn("success_without_review_evidence", similar_games)
        self.assertNotIn("risk_without_review_evidence", similar_games)

    def test_market_payload_filters_noisy_review_keywords(self) -> None:
        topics = pd.DataFrame([
            {"review_sentiment": "negative", "top_terms": "ayy, optimization, es, nie, bug, aaa"},
            {"review_sentiment": "positive", "top_terms": "fun, ayy, entendi tutorial, combat, replayability"},
        ])

        payload = build_market_insight_payload(sample_dataset(), topics, sample_feature_importance())
        recommendations = cast(dict[str, object], payload["recommendations"])

        self.assertEqual(recommendations["development_cautions"], ["optimization", "bug"])
        self.assertEqual(recommendations["positioning_strengths"], ["combat", "replayability"])

    def test_market_payload_separates_strategy_tags_from_genres_and_opportunities(self) -> None:
        data = sample_dataset()
        data.loc[0, "genres"] = "Indie, Free To Play, Early Access, Action"
        data.loc[0, "steam_tags"] = "Indie, Free to Play, Early Access, Multiplayer"
        data.loc[0, "predicted_success_probability"] = 0.9

        payload = build_market_insight_payload(data, pd.DataFrame(), sample_feature_importance())
        developer_inputs = cast(dict[str, object], payload["developer_inputs"])
        developer_guidance = cast(dict[str, object], payload["developer_guidance"])
        market_trends = cast(list[dict[str, object]], payload["market_trends"])
        input_genres = cast(list[str], developer_inputs["genres"])
        input_tags = cast(list[str], developer_inputs["tags"])
        strategy_tags = cast(list[str], developer_inputs["strategy_tags"])
        signals = [str(card["signal"]) for card in cast(list[dict[str, object]], developer_guidance["cards"])]
        trend_names = [str(row["name"]) for row in market_trends]

        self.assertNotIn("Indie", input_genres)
        self.assertNotIn("Free To Play", input_genres)
        self.assertNotIn("Early Access", input_genres)
        self.assertIn("Indie", strategy_tags)
        self.assertIn("Free to Play", strategy_tags)
        self.assertIn("Early Access", strategy_tags)
        self.assertNotIn("Indie", input_tags)
        self.assertNotIn("Free to Play", input_tags)
        self.assertNotIn("Early Access", input_tags)
        self.assertNotIn("Free To Play", signals)
        self.assertNotIn("Free to Play", signals)
        self.assertNotIn("Indie", trend_names)
        self.assertNotIn("Free To Play", trend_names)
        self.assertNotIn("Early Access", trend_names)

    def test_market_payload_keeps_tiny_perfect_terms_out_of_opportunity_signal(self) -> None:
        rows = []
        for index in range(20):
            rows.append({
                "appid": 1000 + index,
                "name": f"Reliable Action {index}",
                "genres": "Action",
                "steam_tags": "Action",
                "categories": "Single-player",
                "success": 1 if index < 12 else 0,
                "predicted_success_probability": 0.74,
                "total_reviews": 300 + index,
                "positive_rate": 0.82,
            })
        for index in range(2):
            rows.append({
                "appid": 2000 + index,
                "name": f"Tiny Perfect {index}",
                "genres": "Tiny Perfect",
                "steam_tags": "Tiny Perfect",
                "categories": "Includes Source SDK",
                "success": 1,
                "predicted_success_probability": 0.99,
                "total_reviews": 50,
                "positive_rate": 1.0,
            })

        payload = build_market_insight_payload(pd.DataFrame(rows), pd.DataFrame())
        trends = cast(list[dict[str, object]], payload["market_trends"])
        tiny = next(row for row in trends if row["name"] == "Tiny Perfect")
        developer_guidance = cast(dict[str, object], payload["developer_guidance"])
        signals = [str(card["signal"]) for card in cast(list[dict[str, object]], developer_guidance["cards"])]

        self.assertEqual(tiny["trend"], "표본 부족")
        self.assertEqual(tiny["sample_status"], "표본 부족")
        self.assertNotIn("Tiny Perfect", signals)
        self.assertIn("Action", signals)

    def test_market_payload_keeps_eligible_trend_when_many_tiny_terms_sort_first(self) -> None:
        rows = []
        for index in range(20):
            rows.append({
                "appid": 5000 + index,
                "name": f"Reliable Action {index}",
                "genres": "Action",
                "steam_tags": "Action",
                "categories": "Single-player",
                "success": 1 if index < 12 else 0,
                "predicted_success_probability": 0.74,
                "total_reviews": 300 + index,
                "positive_rate": 0.82,
            })
        for index in range(70):
            rows.append({
                "appid": 6000 + index,
                "name": f"Tiny Perfect {index}",
                "genres": f"Tiny Perfect {index}",
                "steam_tags": f"Tiny Perfect {index}",
                "categories": "Includes Source SDK",
                "success": 1,
                "predicted_success_probability": 0.99,
                "total_reviews": 50,
                "positive_rate": 1.0,
            })

        payload = build_market_insight_payload(pd.DataFrame(rows), pd.DataFrame())
        trends = cast(list[dict[str, object]], payload["market_trends"])
        trend_names = [str(row["name"]) for row in trends]

        self.assertEqual(trend_names[0], "Action")
        tiny = next(row for row in trends if row["name"] == "Tiny Perfect 0")
        self.assertEqual(tiny["sample_status"], "표본 부족")

    def test_confidence_reports_missing_population_coverage_and_avoids_high_label(self) -> None:
        data = pd.concat([sample_dataset()] * 150, ignore_index=True)
        data["total_reviews"] = 500

        payload = build_market_insight_payload(data, pd.DataFrame(), sample_feature_importance())
        semantic = cast(dict[str, object], payload["semantic_model"])
        confidence = cast(dict[str, object], semantic["confidence"])
        coverage = cast(dict[str, object], confidence["coverage"])

        self.assertNotEqual(confidence["label"], "높음")
        self.assertEqual(coverage["status"], "모집단 coverage 데이터 부족")
        self.assertEqual(coverage["modeled_games"], len(data))

    def test_confidence_uses_release_window_candidate_coverage(self) -> None:
        data = pd.concat([sample_dataset()] * 150, ignore_index=True)
        data["total_reviews"] = 500
        data["release_window_candidate_count"] = 10000

        payload = build_market_insight_payload(data, pd.DataFrame(), sample_feature_importance())
        semantic = cast(dict[str, object], payload["semantic_model"])
        confidence = cast(dict[str, object], semantic["confidence"])
        coverage = cast(dict[str, object], confidence["coverage"])

        self.assertEqual(confidence["label"], "중간")
        self.assertEqual(coverage["release_window_candidates"], 10000)
        self.assertAlmostEqual(float(str(coverage["sample_coverage"])), len(data) / 10000)
        self.assertIn("낮음", str(coverage["status"]))

    def test_external_availability_only_reports_critic_score(self) -> None:
        data = sample_dataset()
        data[["webzine_mentions", "youtube_mentions", "blog_mentions", "external_attention_score"]] = 0

        payload = build_market_insight_payload(data, pd.DataFrame())
        external_data = cast(dict[str, object], payload["external_data"])
        critic_score = cast(dict[str, object], external_data["critic_score"])

        self.assertEqual(set(external_data), {"critic_score"})
        self.assertFalse(critic_score["enabled"])
        self.assertIn("평점", str(critic_score["reason"]))

    def test_steamspy_owner_proxy_is_not_reported_in_market_payload(self) -> None:
        data = sample_dataset()
        data["steamspy_owners_median"] = [1000, 0, 2000, 0]

        payload = build_market_insight_payload(data, pd.DataFrame())
        external_data = cast(dict[str, object], payload["external_data"])

        self.assertNotIn("steamspy", external_data)

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
        self.assertIn("filterInputGroup", html)
        self.assertIn("showMoreInputGroup", html)
        self.assertIn("data-input-group", html)
        self.assertIn("검색", html)
        self.assertIn("더보기", html)
        self.assertIn("조합 단위 집계 모델", html)
        self.assertIn("renderGuidance", html)
        self.assertIn("출시 전 체크리스트", html)

    def test_static_html_contains_game_list_modal_and_impact_chips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame())
            html = output.read_text(encoding="utf-8")

        self.assertIn("selectedGames", html)
        self.assertIn("tagComboRecommendations", html)
        self.assertIn("선택 장르 기준 추천 태그 조합", html)
        self.assertIn("maximizePlanButton", html)
        self.assertIn("선택 조건 최적화", html)
        self.assertIn("optimizePlanningInputs", html)
        self.assertIn("tagComboCandidates", html)
        self.assertIn("renderTagComboRecommendations", html)
        self.assertIn("gameModal", html)
        self.assertIn("openGameDetail", html)
        self.assertIn("renderImpactChips", html)
        self.assertIn("data-impact-disabled", html)
        self.assertIn("feature importance", html)
        self.assertIn("리뷰 성장률", html)
        self.assertIn("조합 단위 집계 모델", html)
        self.assertIn("모집단 coverage", html)
        self.assertIn("renderSemanticModel", html)
        self.assertIn("reference_reason", html)
        self.assertNotIn("리뷰 근거 없는 참고", html)
        self.assertNotIn("리뷰 근거 있는 참고", html)
        self.assertNotIn("리뷰 본문 표본이", html)
        self.assertIn("semanticProfileText", html)
        self.assertIn("항목별 신뢰도", html)

    def test_static_html_renders_four_part_developer_diagnosis_and_sample_gated_recommendations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame())
            html = output.read_text(encoding="utf-8")

        self.assertIn("renderFourPartDiagnosis", html)
        self.assertIn("성공 가능성", html)
        self.assertIn("비교군", html)
        self.assertIn("관측 실패/주의 사례", html)
        self.assertIn("액션 제안", html)
        self.assertIn("strongRecommendationMinimumSample", html)
        self.assertIn("충분 표본 기반 추천", html)
        self.assertIn("탐색 후보 / 표본 부족", html)

    def test_static_html_contains_tabs_balanced_cards_images_and_explanations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn("tab-button", html)
        self.assertIn("tab-panel", html)
        self.assertIn("선택 조건 기반 참고 게임", html)
        self.assertIn("successReferenceGames", html)
        self.assertIn("riskReferenceGames", html)
        self.assertIn("payload.similar_games.success_examples", html)
        self.assertIn("reference_reason", html)
        self.assertIn("header_image", html)
        self.assertIn("createGameImage", html)
        self.assertIn("importance_description", html)
        self.assertIn("featureHelpText", html)
        self.assertIn("선택 전 기준선", html)

    def test_model_opinion_uses_configured_outcome_thresholds(self) -> None:
        data = sample_dataset()
        data.loc[0, "predicted_success_probability"] = SETTINGS.outcome_success_probability_threshold
        data.loc[1, "predicted_success_probability"] = SETTINGS.outcome_mid_probability_threshold

        payload = build_market_insight_payload(data, pd.DataFrame(), sample_feature_importance())
        games = cast(list[dict[str, object]], payload["games"])
        success_game = next(game for game in games if game["appid"] == 10)
        mid_game = next(game for game in games if game["appid"] == 20)

        self.assertEqual(success_game["outcome_label"], "성공")
        self.assertIn("관측 결과 성공 사례", str(success_game["model_opinion"]))
        self.assertEqual(mid_game["outcome_label"], "중박")
        self.assertIn("관측 결과", str(mid_game["model_opinion"]))

    def test_reporting_rules_document_market_insight_domain_constants(self) -> None:
        rules = Path("docs/REPORTING_RULES.md").read_text(encoding="utf-8")

        self.assertIn("GENRE_LIKE_TAGS", rules)
        self.assertIn("STRATEGY_TAG_NAMES", rules)
        self.assertIn("NOISY_REVIEW_TERMS", rules)

    def test_report_threshold_literals_only_live_in_config(self) -> None:
        source_paths = [Path("src/steam_success/market_insight.py"), Path("src/steam_success/market_report.py")]
        for source_path in source_paths:
            text = source_path.read_text(encoding="utf-8")
            self.assertNotIn("0.65", text)
            self.assertNotIn("0.35", text)

    def test_static_html_uses_configured_outcome_threshold_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        success_label = f"성공: {SETTINGS.outcome_success_probability_threshold:.0%} 이상"
        mid_label = f"중박: {SETTINGS.outcome_mid_probability_threshold:.0%} 이상 {SETTINGS.outcome_success_probability_threshold:.0%} 미만"
        fail_label = f"실패: {SETTINGS.outcome_mid_probability_threshold:.0%} 미만"
        self.assertIn(success_label, html)
        self.assertIn(mid_label, html)
        self.assertIn(fail_label, html)

    def test_static_html_documents_criteria_trends_and_blank_planning_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn("성공/중박/실패 기준", html)
        self.assertIn(f"성공: {SETTINGS.outcome_success_probability_threshold:.0%} 이상", html)
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
        self.assertIn("성장 조합", html)
        self.assertIn("내 기획 진단", html)
        self.assertIn("근거 사례", html)
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
        special = next(game for game in games if game["name"] == "A & B </script> <Test>")
        self.assertEqual(special["total_reviews"], 0)
        self.assertEqual(special["predicted_success_probability"], 0.0)


    def test_developer_planner_uses_prediction_only_for_selected_concept(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        match = re.search(r'<script id="market-data" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(match)
        if match is None:
            self.fail("market data payload script is missing")
        payload = json.loads(match.group(1))
        games = cast(list[dict[str, object]], payload["games"])

        self.assertIn("combination_opportunities", payload)
        self.assertIn("기획 잠재력", html)
        self.assertIn("근거 표본", html)
        self.assertIn("관측 결과", html)
        self.assertNotIn("모델 예측 성공확률", html)
        self.assertNotIn("add(card, node('p', `예측", html)
        self.assertTrue(all("estimated_success_probability" not in game for game in games))
        self.assertTrue(all("observed_success_rate" in row for row in cast(list[dict[str, object]], payload["combination_opportunities"])))

    def test_sparse_combination_is_exploratory_not_recommended(self) -> None:
        rows = []
        for index in range(2):
            rows.append({
                "appid": 2000 + index,
                "name": f"Sparse Combo {index}",
                "genres": "Sparse",
                "steam_tags": "Sparse, Novel",
                "categories": "Single-player",
                "success": 1,
                "predicted_success_probability": 0.99,
                "total_reviews": 40,
                "positive_rate": 0.95,
                "reviews_30d": 20,
                "reviews_90d": 40,
            })

        payload = build_market_insight_payload(pd.DataFrame(rows), pd.DataFrame(), sample_feature_importance())
        opportunities = cast(list[dict[str, object]], payload["combination_opportunities"])
        sparse = next(row for row in opportunities if row["combination"] == "Sparse + Novel")

        self.assertFalse(bool(sparse["rank_eligible"]))
        self.assertEqual(sparse["growth_label"], "탐색 후보 / 표본 부족")
        self.assertIn("강한 추천을 하지 않습니다", " ".join(cast(list[str], sparse["evidence_lines"])))

    def test_growth_combinations_rank_by_sample_smoothed_success_and_review_growth(self) -> None:
        rows = []
        for index in range(24):
            rows.append({
                "appid": 3000 + index,
                "name": f"Growing Action {index}",
                "genres": "Action",
                "steam_tags": "Action, Co-op",
                "categories": "Single-player",
                "success": 1 if index < 12 else 0,
                "predicted_success_probability": 0.5,
                "total_reviews": 200 + index,
                "positive_rate": 0.8,
                "reviews_30d": 20,
                "reviews_90d": 160,
                "release_year": 2026,
            })
        for index in range(24):
            rows.append({
                "appid": 4000 + index,
                "name": f"Flat Puzzle {index}",
                "genres": "Puzzle",
                "steam_tags": "Puzzle, Cozy",
                "categories": "Single-player",
                "success": 1 if index < 12 else 0,
                "predicted_success_probability": 0.5,
                "total_reviews": 200 + index,
                "positive_rate": 0.8,
                "reviews_30d": 100,
                "reviews_90d": 110,
                "release_year": 2025,
            })
        for index in range(2):
            rows.append({
                "appid": 5000 + index,
                "name": f"Tiny Perfect {index}",
                "genres": "Tiny Perfect",
                "steam_tags": "Tiny Perfect, Viral",
                "categories": "Single-player",
                "success": 1,
                "predicted_success_probability": 1.0,
                "total_reviews": 50,
                "positive_rate": 1.0,
                "reviews_30d": 10,
                "reviews_90d": 100,
                "release_year": 2026,
            })

        payload = build_market_insight_payload(pd.DataFrame(rows), pd.DataFrame(), sample_feature_importance())
        opportunities = cast(list[dict[str, object]], payload["combination_opportunities"])
        eligible = [row for row in opportunities if bool(row["rank_eligible"])]
        tiny = next(row for row in opportunities if row["combination"] == "Tiny Perfect + Viral")

        self.assertEqual(eligible[0]["combination"], "Action + Co-op")
        self.assertGreater(float(str(eligible[0]["review_growth_ratio"])), float(str(eligible[1]["review_growth_ratio"])))
        self.assertFalse(bool(tiny["rank_eligible"]))
        self.assertEqual(tiny["growth_label"], "탐색 후보 / 표본 부족")


    def test_market_site_initial_render_targets_exist_and_strategy_tags_are_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn('id="semanticModel"', html)
        self.assertIn("const selectedState = { genres:new Set(), strategy_tags:new Set(), tags:new Set() };", html)
        self.assertIn("const stateSet = selectedSet(type);", html)
        self.assertNotIn("selectedState[type].has(value)", html)

    def test_growth_combinations_render_as_readable_cards_not_dense_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn("opportunity-list", html)
        self.assertIn("opportunity-card", html)
        self.assertIn("score-badge", html)
        self.assertIn("evidence-list", html)
        self.assertIn("renderOpportunityCards", html)
        self.assertNotIn("모델 기획 잠재력", html)
        self.assertIn("관측 결과", html)


    def test_market_site_keeps_low_impact_options_selectable_and_styles_dense_controls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn("input[type=\"search\"]", html)
        self.assertIn(".table-wrap", html)
        self.assertIn(":focus-visible", html)
        self.assertIn("aria-selected", html)
        self.assertIn("button.disabled = !active && !hasGames;", html)
        self.assertNotIn("impact < 0.005", html)


    def test_market_site_planner_explains_baseline_and_links_diagnosis_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn("planningActions", html)
        self.assertIn("선택 조건 최적화", html)
        self.assertIn("선택 전 기준선", html)
        self.assertIn("전체 관측 성공률", html)
        self.assertIn("scrollToPlannerReference('selectedGames')", html)
        self.assertIn("scrollToPlannerReference('riskReferenceGames')", html)
        self.assertIn("선택 참고게임 보기", html)
        self.assertIn("선택 실패/주의 사례 보기", html)
        self.assertNotIn("근거 사례 보기", html)
        self.assertIn("관측 실패/주의 사례", html)
        self.assertNotIn("위험 사례", html)

    def test_market_site_handles_missing_images_external_data_and_architecture_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_market_insight_site(Path(temp_dir), sample_dataset(), pd.DataFrame(), sample_feature_importance())
            html = output.read_text(encoding="utf-8")

        self.assertIn("image-placeholder", html)
        self.assertIn("이미지 없음", html)
        self.assertIn("renderModelArchitecture", html)
        self.assertIn("modelArchitecture", html)
        self.assertIn("모델·파이프라인 구조", html)
        self.assertIn("value.enabled", html)
        self.assertIn("표시 가능한 평점 서비스 데이터가 없습니다", html)
        self.assertIn("renderTrendTable", html)
        self.assertIn("table-wrap", html)


if __name__ == "__main__":
    unittest.main()
