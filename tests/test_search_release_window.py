from __future__ import annotations

import unittest
from unittest.mock import patch

from steam_success.collect.search_release_window import _fetch_search_page, _parse_rows


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, object] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.url = "https://store.steampowered.com/search/results/?start=0"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"status={self.status_code}")

    def json(self) -> dict[str, object]:
        return self._payload


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls = 0

    def get(self, *_args: object, **_kwargs: object) -> FakeResponse:
        response = self.responses[self.calls]
        self.calls += 1
        return response


class SearchReleaseWindowTests(unittest.TestCase):
    def test_parse_rows_adds_year_bucket(self) -> None:
        payload = {
            "results_html": """
            <a class="search_result_row" data-ds-appid="1">
              <span class="title">A</span>
              <div class="search_released">May 31, 2026</div>
            </a>
            <a class="search_result_row" data-ds-appid="2">
              <span class="title">B</span>
              <div class="search_released">Jan 18, 2025</div>
            </a>
            <a class="search_result_row" data-ds-appid="3">
              <span class="title">C</span>
              <div class="search_released">Dec 4, 2024</div>
            </a>
            """
        }
        rows = _parse_rows(payload, "https://example.test", 0, 2025, 2026)
        self.assertEqual([row["release_year_bucket"] for row in rows], ["2026", "2025", "out_of_range"])
        self.assertEqual(rows[1]["release_window_role"], "2025_trend_label_candidate")

    def test_fetch_page_retries_after_429(self) -> None:
        session = FakeSession([
            FakeResponse(429),
            FakeResponse(200, {"total_count": 1, "results_html": ""}),
        ])
        with patch("steam_success.collect.search_release_window.time.sleep", return_value=None):
            payload, _url = _fetch_search_page(
                session=session,  # type: ignore[arg-type]
                start=0,
                count=100,
                country="US",
                language="english",
                sleep_seconds=1.5,
                max_retries=2,
            )
        self.assertEqual(payload["total_count"], 1)
        self.assertEqual(session.calls, 2)


if __name__ == "__main__":
    unittest.main()
