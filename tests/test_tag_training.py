from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from steam_success.tag_training import TagTrainingConfig, _dedupe_tag_rows, _existing_seen, _load_popular_tags, _apply_relative_success, _page_has_cutoff_year, _page_sequence, _release_year, _sample_sort_counts, _search_rows_for_model, _sort_targets, _tag_batch, _tag_memberships, _tag_summary


def fail_fetch_popular_tags(_config: TagTrainingConfig) -> pd.DataFrame:
    raise RuntimeError("tag endpoint unavailable")


class TagTrainingTests(unittest.TestCase):
    def test_release_year_parses_steam_formats(self) -> None:
        self.assertEqual(_release_year("Dec 31, 2025"), 2025)
        self.assertEqual(_release_year("Dec 2025"), 2025)
        self.assertEqual(_release_year("2025"), 2025)
        self.assertIsNone(_release_year("Coming soon"))

    def test_load_popular_tags_uses_cached_csv_when_endpoint_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = Path(temp_dir)
            pd.DataFrame([{"tag_id": 1, "tag_name": "Action"}]).to_csv(raw_dir / "steam_popular_tags.csv", index=False)

            with patch("steam_success.tag_training.fetch_popular_tags", fail_fetch_popular_tags):
                tags = _load_popular_tags(raw_dir, TagTrainingConfig(max_tags=1))

        self.assertEqual(tags.loc[0, "tag_name"], "Action")

    def test_page_has_cutoff_year_detects_2025_rows(self) -> None:
        html = '<a class="search_result_row"><div class="search_released">Jan 1, 2026</div></a><a class="search_result_row"><div class="search_released">Dec 31, 2025</div></a>'

        self.assertTrue(_page_has_cutoff_year(html, 2025))
        self.assertFalse(_page_has_cutoff_year(html.replace("Dec 31, 2025", "Jan 2, 2026"), 2025))

    def test_mixed_sort_targets_split_bias_reduction_frames(self) -> None:
        targets = _sort_targets(TagTrainingConfig(games_per_tag=50, sort_by="mixed"))

        self.assertEqual(targets, [("Released_DESC", 15), ("Reviews_DESC", 15), ("Price_ASC", 10), ("Price_DESC", 10)])

    def test_tag_batch_limits_collection_window(self) -> None:
        tags = pd.DataFrame([
            {"tag_id": 1, "tag_name": "Action"},
            {"tag_id": 2, "tag_name": "RPG"},
            {"tag_id": 3, "tag_name": "Simulation"},
            {"tag_id": 4, "tag_name": "Puzzle"},
        ])

        batch = _tag_batch(tags, TagTrainingConfig(tag_offset=1, tag_limit=2))

        self.assertEqual(batch["tag_name"].tolist(), ["RPG", "Simulation"])

    def test_resume_helpers_reuse_existing_tag_rows(self) -> None:
        rows = pd.DataFrame([
            {"appid": 10, "tag_id": 1, "tag_name": "Action", "sample_sort": "Released_DESC"},
            {"appid": 10, "tag_id": 1, "tag_name": "Action", "sample_sort": "Released_DESC"},
            {"appid": 20, "tag_id": 2, "tag_name": "RPG", "sample_sort": "Reviews_DESC"},
        ])

        deduped = _dedupe_tag_rows(rows)

        self.assertEqual(len(deduped), 2)
        self.assertEqual(_existing_seen(deduped, 1), {10})

    def test_page_sequence_uses_bands_for_non_release_sorts(self) -> None:
        self.assertEqual(_page_sequence(150, 3, "Released_DESC"), [150, 151, 152])
        self.assertEqual(_page_sequence(1, 5, "Reviews_DESC"), [1, 2, 4, 8, 16])

    def test_relative_success_uses_tag_threshold_not_absolute_only(self) -> None:
        dataset = pd.DataFrame([
            {"appid": 1, "success": 0, "total_reviews": 1000, "positive_rate": 0.9},
            {"appid": 2, "success": 1, "total_reviews": 200, "positive_rate": 0.95},
            {"appid": 3, "success": 0, "total_reviews": 50, "positive_rate": 0.95},
        ])
        tag_rows = pd.DataFrame([
            {"appid": 1, "tag_id": 19, "tag_name": "Action", "sample_sort": "Reviews_DESC"},
            {"appid": 2, "tag_id": 19, "tag_name": "Action", "sample_sort": "Released_DESC"},
            {"appid": 3, "tag_id": 19, "tag_name": "Action", "sample_sort": "Released_DESC"},
        ])

        labeled = _apply_relative_success(dataset, tag_rows, TagTrainingConfig(relative_success_quantile=0.5, relative_positive_rate_threshold=0.75))

        self.assertEqual(labeled["success"].tolist(), [1, 1, 0])
        self.assertEqual(labeled["absolute_success"].tolist(), [0, 1, 0])

    def test_sample_sort_counts_records_sampling_mix(self) -> None:
        tag_rows = pd.DataFrame([
            {"appid": 1, "tag_id": 19, "tag_name": "Action", "sample_sort": "Reviews_DESC"},
            {"appid": 2, "tag_id": 19, "tag_name": "Action", "sample_sort": "Released_DESC"},
            {"appid": 3, "tag_id": 19, "tag_name": "Action", "sample_sort": "Released_DESC"},
        ])

        counts = _sample_sort_counts(tag_rows)

        self.assertIn("Reviews_DESC=1", str(counts.loc[0, "sample_breakdown"]))
        self.assertIn("Released_DESC=2", str(counts.loc[0, "sample_breakdown"]))

    def test_tag_memberships_deduplicate_appids(self) -> None:
        rows = pd.DataFrame([
            {"appid": 1, "tag_id": 19, "tag_name": "Action"},
            {"appid": 1, "tag_id": 122, "tag_name": "RPG"},
            {"appid": 1, "tag_id": 19, "tag_name": "Action"},
        ])

        memberships = _tag_memberships(rows)

        self.assertEqual(str(memberships.loc[0, "steam_tags"]), "Action, RPG")
        self.assertEqual(int(str(memberships.loc[0, "steam_tag_count"])), 2)

    def test_tag_summary_records_shortfall_without_fabricating_rows(self) -> None:
        coverage = pd.DataFrame([{"tag_id": 19, "tag_name": "Action", "requested_games": 50, "collected_games": 3}])
        tag_rows = pd.DataFrame([
            {"appid": 1, "tag_id": 19, "tag_name": "Action"},
            {"appid": 2, "tag_id": 19, "tag_name": "Action"},
            {"appid": 3, "tag_id": 19, "tag_name": "Action"},
        ])
        dataset = pd.DataFrame([
            {"appid": 1, "success": 1, "positive_rate": 0.9, "total_reviews": 1000},
            {"appid": 2, "success": 0, "positive_rate": 0.6, "total_reviews": 100},
        ])

        summary = _tag_summary(dataset, tag_rows, coverage)

        self.assertEqual(int(str(summary.loc[0, "requested_games"])), 50)
        self.assertEqual(int(str(summary.loc[0, "collected_games"])), 3)
        self.assertEqual(int(str(summary.loc[0, "trained_games"])), 2)

    def test_search_rows_for_model_keeps_one_row_per_appid(self) -> None:
        rows = pd.DataFrame([
            {"appid": 2, "tag_name": "RPG", "search_name": "B", "search_release_text": "2025", "search_price_text": "$1", "search_page": 1, "source_url": "u"},
            {"appid": 2, "tag_name": "Action", "search_name": "B", "search_release_text": "2025", "search_price_text": "$1", "search_page": 1, "source_url": "u"},
        ])

        search = _search_rows_for_model(rows)

        self.assertEqual(len(search), 1)
        self.assertEqual(search.columns.tolist(), ["appid", "search_name", "search_release_text", "search_price_text", "search_page", "source_url"])


if __name__ == "__main__":
    unittest.main()
