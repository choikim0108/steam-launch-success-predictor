from __future__ import annotations

import unittest

import pandas as pd

from steam_success.collect.review_histogram import _completed_appids


class ReviewHistogramTests(unittest.TestCase):
    def test_completed_appids_only_includes_successful_rows(self) -> None:
        status = pd.DataFrame(
            [
                {"appid": 1, "histogram_success": True},
                {"appid": 2, "histogram_success": False},
                {"appid": 3, "histogram_success": "True"},
                {"appid": 4, "histogram_success": "False"},
            ]
        )

        self.assertEqual(_completed_appids(status), {1, 3})


if __name__ == "__main__":
    unittest.main()
