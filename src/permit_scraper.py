"""OpenGov-style public permit scraper."""

from __future__ import annotations

import asyncio
import csv
import json
from datetime import datetime
from typing import Any

from playwright.async_api import Browser, Page, async_playwright


class OpenGovPermitScraper:
    """Scrape public permit records from an OpenGov search portal."""

    def __init__(self, base_url: str = "https://conroetx.portal.opengov.com", headless: bool = True):
        self.base_url = base_url.rstrip("/")
        self.search_url = f"{self.base_url}/search"
        self.headless = headless
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.playwright = None

    async def start(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()

    async def close(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def search_permits(self, query: str = "building") -> list[dict[str, Any]]:
        if not self.page:
            raise RuntimeError("Scraper has not been started")

        print(f"[{datetime.now()}] searching public permits: {query}")
        await self.page.goto(self.search_url)
        await self.page.wait_for_load_state("networkidle")

        records_tab = self.page.get_by_role("tab", name="Records")
        await records_tab.click()
        await asyncio.sleep(1)

        search_box = self.page.get_by_role("searchbox", name="Search for a record")
        await search_box.fill(query)
        await search_box.press("Enter")
        await asyncio.sleep(3)

        permits: list[dict[str, Any]] = []
        results = await self.page.locator('a[href^="/records/"]').all()
        for result in results:
            try:
                href = await result.get_attribute("href")
                text = await result.inner_text()
                lines = text.strip().split("\n")
                permit_number = lines[0] if lines else ""
                permit_type = lines[1] if len(lines) > 1 else ""
                permits.append(
                    {
                        "permit_number": permit_number,
                        "permit_type": permit_type,
                        "url": f"{self.base_url}{href}",
                        "record_id": href.split("/")[-1] if href else "",
                    }
                )
            except Exception as exc:
                print(f"Skipping permit result after parse error: {exc}")

        print(f"[{datetime.now()}] found {len(permits)} permit links")
        return permits

    async def get_permit_details(self, permit_url: str) -> dict[str, Any]:
        if not self.page:
            raise RuntimeError("Scraper has not been started")

        print(f"[{datetime.now()}] fetching details: {permit_url}")
        await self.page.goto(permit_url)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        details: dict[str, Any] = {"url": permit_url}
        details["location"] = await self._text_near_heading("h3", ", TX")
        details["created_date"] = await self._field_text("Created")
        details["status"] = await self._field_text("Status")
        details["estimated_cost"] = await self._field_text("Estimated Project Cost")
        details["contractor_company"] = await self._field_text("Company Name")
        details["contractor_phone"] = await self._field_text("Phone Number")
        details["contractor_email"] = await self._field_text("Email Address")
        details["project_type"] = await self._field_text("Project Type")
        details["description"] = await self._field_text("Description of Work")

        first_name = await self._field_text("First Name")
        last_name = await self._field_text("Last Name")
        if first_name or last_name:
            details["contractor_name"] = f"{first_name} {last_name}".strip()

        return {key: value for key, value in details.items() if value}

    async def scrape(self, max_permits: int = 50, query: str = "building") -> list[dict[str, Any]]:
        await self.start()
        try:
            permits = (await self.search_permits(query))[:max_permits]
            records: list[dict[str, Any]] = []
            for index, permit in enumerate(permits, 1):
                print(f"[{index}/{len(permits)}] processing {permit.get('permit_number')}")
                details = await self.get_permit_details(permit["url"])
                details.update(permit)
                records.append(details)
                await asyncio.sleep(2)
            return records
        finally:
            await self.close()

    async def _field_text(self, label: str) -> str:
        if not self.page:
            return ""
        element = self.page.locator(f"text={label}").first
        if await element.count() == 0:
            return ""
        parent = element.locator("xpath=..")
        paragraph = parent.locator("p")
        if await paragraph.count() == 0:
            return ""
        return (await paragraph.first.inner_text()).strip()

    async def _text_near_heading(self, selector: str, contains: str) -> str:
        if not self.page:
            return ""
        element = self.page.locator(selector).filter(has_text=contains).first
        if await element.count() == 0:
            return ""
        return (await element.inner_text()).strip()


def save_json(records: list[dict[str, Any]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)


def save_csv(records: list[dict[str, Any]], path: str) -> None:
    if not records:
        return
    keys = sorted({key for record in records for key in record})
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)
