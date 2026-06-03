from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from steam_success.collect.external_web import _gdelt_webzine_mentions, _steamspy_owners_median, _webzine_mentions, _webzine_source_count


class ExternalWebTests(unittest.TestCase):
    def test_steamspy_owners_median_parses_range(self) -> None:
        response = Mock()
        response.json.return_value = {"owners": "20,000 .. 50,000"}
        response.raise_for_status.return_value = None

        with patch("steam_success.collect.external_web.requests.get", return_value=response):
            owners = _steamspy_owners_median(10)

        self.assertEqual(owners, 35000)

    def test_webzine_mentions_searches_each_domain(self) -> None:
        html = '<li class="b_algo"><h2><a>Review A</a></h2></li><li class="b_algo"><h2><a>Review B</a></h2></li>'

        with patch("steam_success.collect.external_web._gdelt_webzine_mentions", return_value=(0, "")), patch("steam_success.collect.external_web._search_html", return_value=html) as search:
            count, titles = _webzine_mentions("Test Game", ("ign.com", "pcgamer.com"))

        self.assertEqual(count, 2)
        self.assertEqual(search.call_count, 1)
        self.assertIn("Review A", titles)

    def test_gdelt_webzine_mentions_parses_articles(self) -> None:
        response = Mock()
        response.json.return_value = {"articles": [{"title": "Test Game review"}, {"title": "Test Game impressions"}]}
        response.raise_for_status.return_value = None

        with patch("steam_success.collect.external_web.requests.get", return_value=response) as get:
            count, titles = _gdelt_webzine_mentions("Test Game", ("pcgamer.com", "ign.com"))

        self.assertEqual(count, 2)
        self.assertIn("Test Game review", titles)
        self.assertIn("api.gdeltproject.org", get.call_args.args[0])

    def test_webzine_source_count_detects_reachable_feeds(self) -> None:
        response = Mock()
        response.text = "<rss><channel><item><title>Game Review</title></item></channel></rss>"
        response.raise_for_status.return_value = None

        with patch("steam_success.collect.external_web.requests.get", return_value=response):
            count = _webzine_source_count()

        self.assertGreaterEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
