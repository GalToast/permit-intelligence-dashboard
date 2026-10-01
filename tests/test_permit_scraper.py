"""Tests for the Playwright-optional scraper import.

``permit_scraper`` must import without Playwright installed, and starting the
scraper without it must fail with a helpful message instead of an ImportError.
The missing-Playwright case is forced deterministically via ``sys.modules`` so
these tests pass in environments with and without Playwright installed.
"""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from permit_scraper import OpenGovPermitScraper  # noqa: E402


class ScraperImportTests(unittest.TestCase):
    def test_module_imports_without_playwright(self):
        self.assertIsNone(OpenGovPermitScraper().browser)
        self.assertIsNone(OpenGovPermitScraper().page)

    def test_scraper_instantiates_without_launching_browser(self):
        scraper = OpenGovPermitScraper(base_url="https://example.com", headless=True)
        self.assertEqual(scraper.search_url, "https://example.com/search")
        self.assertIsNone(scraper.browser)

    def test_start_without_playwright_raises_helpful_error(self):
        scraper = OpenGovPermitScraper()
        with patch.dict(sys.modules, {"playwright": None, "playwright.async_api": None}):
            with self.assertRaisesRegex(
                RuntimeError, r"Playwright is not installed.*requirements-scrape\.txt"
            ):
                asyncio.run(scraper.start())

    def test_save_helpers_do_not_need_playwright(self):
        from permit_scraper import save_json, save_csv

        records = [{"permit_number": "P-1", "url": "https://example.com/records/1"}]
        with patch.dict(sys.modules, {"playwright": None, "playwright.async_api": None}):
            save_json(records, str(ROOT / "tests" / ".tmp_out.json"))
            save_csv(records, str(ROOT / "tests" / ".tmp_out.csv"))
        (ROOT / "tests" / ".tmp_out.json").unlink()
        (ROOT / "tests" / ".tmp_out.csv").unlink()


if __name__ == "__main__":
    unittest.main()
