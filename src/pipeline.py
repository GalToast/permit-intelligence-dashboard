"""End-to-end permit intelligence pipeline."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
from datetime import datetime
from typing import Any

from parcel_client import PublicParcelClient
from permit_scraper import OpenGovPermitScraper


TARGET_PERMIT_TYPES = [
    "Commercial Building",
    "Commercial Alteration",
    "Residential Building",
    "New Construction",
    "Addition",
]


class PermitIntelligencePipeline:
    """Scrape, enrich, score, filter, and export public permit records."""

    def __init__(
        self,
        portal_base_url: str = "https://conroetx.portal.opengov.com",
        min_cost: float = 50000,
        headless: bool = True,
    ) -> None:
        self.min_cost = min_cost
        self.scraper = OpenGovPermitScraper(base_url=portal_base_url, headless=headless)
        self.parcels = PublicParcelClient()

    async def run(self, max_permits: int = 50) -> list[dict[str, Any]]:
        print("=" * 80)
        print(f"Permit intelligence pipeline - {datetime.now():%Y-%m-%d %H:%M:%S}")
        print("=" * 80)

        permits = await self.scraper.scrape(max_permits=max_permits)
        enriched = [self._enrich(record) for record in permits]
        filtered = [self._score(record) for record in enriched if self._is_relevant(record)]
        filtered.sort(key=lambda record: record.get("opportunity_score", 0), reverse=True)
        return filtered

    def _enrich(self, permit: dict[str, Any]) -> dict[str, Any]:
        record = permit.copy()
        address = extract_street_address(record.get("location", ""))
        if address:
            parcel = self.parcels.query_by_address(address)
            if parcel:
                record["parcel_data"] = parcel
        return record

    def _is_relevant(self, permit: dict[str, Any]) -> bool:
        permit_type = permit.get("permit_type", "").lower()
        project_type = permit.get("project_type", "").lower()
        relevant_type = any(
            target.lower() in permit_type or target.lower() in project_type
            for target in TARGET_PERMIT_TYPES
        )
        return relevant_type or parse_money(permit.get("estimated_cost", "")) >= self.min_cost

    def _score(self, permit: dict[str, Any]) -> dict[str, Any]:
        record = permit.copy()
        cost = parse_money(record.get("estimated_cost", ""))
        permit_type = record.get("permit_type", "").lower()
        project_type = record.get("project_type", "").lower()
        status = record.get("status", "").lower()

        score = 0
        if cost >= 500000:
            score += 40
        elif cost >= 200000:
            score += 30
        elif cost >= 100000:
            score += 20
        elif cost >= self.min_cost:
            score += 10

        if "commercial" in permit_type or "commercial" in project_type:
            score += 25

        if status in {"pending", "in progress"}:
            score += 20
        elif status == "approved":
            score += 15
        elif status == "complete":
            score += 5

        if record.get("contractor_phone") or record.get("contractor_email"):
            score += 15

        record["estimated_cost_numeric"] = cost
        record["is_commercial"] = "commercial" in permit_type or "commercial" in project_type
        record["has_contractor_info"] = bool(record.get("contractor_company") or record.get("contractor_name"))
        record["opportunity_score"] = min(score, 100)
        return record


def extract_street_address(location: str) -> str:
    return re.sub(r"\s+[A-Z ]+,\s*[A-Z]{2}\s+\d{5}.*$", "", location, flags=re.IGNORECASE).strip()


def parse_money(value: Any) -> float:
    try:
        return float(str(value).replace("$", "").replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def write_outputs(records: list[dict[str, Any]]) -> None:
    with open("filtered_opportunities.json", "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)

    if records:
        keys = sorted({key for record in records for key in record if key != "parcel_data"})
        with open("filtered_opportunities.csv", "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=keys)
            writer.writeheader()
            writer.writerows({key: record.get(key, "") for key in keys} for record in records)


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="Run public permit intelligence pipeline.")
    parser.add_argument("--portal", default="https://conroetx.portal.opengov.com")
    parser.add_argument("--max-permits", type=int, default=25)
    parser.add_argument("--min-cost", type=float, default=50000)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    pipeline = PermitIntelligencePipeline(
        portal_base_url=args.portal,
        min_cost=args.min_cost,
        headless=args.headless,
    )
    records = await pipeline.run(max_permits=args.max_permits)
    write_outputs(records)
    print(f"Exported {len(records)} scored opportunities")


if __name__ == "__main__":
    asyncio.run(async_main())
