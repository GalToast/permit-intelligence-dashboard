"""Public ArcGIS parcel lookup client.

The default endpoint targets public City of Conroe parcel data. No API key is
required for the included endpoint.
"""

from __future__ import annotations

import time
from typing import Any

import requests


class PublicParcelClient:
    """Small wrapper around an ArcGIS REST MapServer query endpoint."""

    def __init__(
        self,
        base_url: str = "https://maps.cityofconroe.org/cvharcgis/rest/services",
        map_service: str = "Building_Inspections_and_Permits/MapServer",
        parcel_layer: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.map_service = map_service.strip("/")
        self.parcel_layer = parcel_layer
        self.session = requests.Session()

    @property
    def layer_url(self) -> str:
        return f"{self.base_url}/{self.map_service}/{self.parcel_layer}"

    def query_by_address(self, address: str) -> dict[str, Any] | None:
        """Return the first parcel match for a street address."""
        if not address.strip():
            return None

        params = {
            "where": f"situs LIKE '%{address.upper()}%'",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json",
            "resultRecordCount": 5,
        }

        try:
            response = self.session.get(f"{self.layer_url}/query", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            print(f"ArcGIS query failed: {exc}")
            return None

        features = data.get("features") or []
        if not features:
            return None

        return self._format_parcel(features[0].get("attributes", {}))

    def batch_query(self, addresses: list[str], delay_seconds: float = 0.5) -> list[dict[str, Any]]:
        """Query several addresses with a simple delay between requests."""
        results: list[dict[str, Any]] = []
        for index, address in enumerate(addresses, 1):
            print(f"[{index}/{len(addresses)}] parcel lookup: {address}")
            parcel = self.query_by_address(address)
            if parcel:
                results.append(parcel)
            time.sleep(delay_seconds)
        return results

    @staticmethod
    def _format_parcel(attributes: dict[str, Any]) -> dict[str, Any]:
        return {
            "parcel_id": attributes.get("PARCELID", ""),
            "situs_address": attributes.get("situs", ""),
            "owner_name": attributes.get("ownerName", ""),
            "improvement_area": attributes.get("imprvMainArea", ""),
            "land_value": attributes.get("landValue", ""),
            "improvement_value": attributes.get("imprvValue", ""),
            "total_value": attributes.get("totalValue", ""),
            "year_built": attributes.get("yearBuilt", ""),
            "acreage": attributes.get("acreage", ""),
            "subdivision": attributes.get("subdivision", ""),
        }
