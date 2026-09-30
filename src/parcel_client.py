"""Public ArcGIS parcel lookup client.

The default endpoint targets public City of Conroe parcel/address data. No API
key is required for the included endpoint.

Data-source status (verified 2026-09-30 via live REST queries):
- MapServer layer 2 (``Conroe_Parcels``, the polygon parcel layer) publishes
  43,348 features but ships every attribute field (PIN, pid, situs, ownerName,
  ownerAddress, imprvActualYearBuilt, imprvMainArea, legalDescription, ...)
  blank or zero. Address matching against it silently returns nothing, so it
  is NOT used as the default enrichment source.
- MapServer layer 1 (``Conroe_Address_Point_Public_View``) is populated with
  47,905 address points and is the default enrichment source. Queries match on
  the ``ADDRESS`` field, and parcel-side attributes come back under truncated
  10-character field names (e.g. ``ownerAddre``, ``imprvActua``).

The field mapping below accepts both the truncated layer-1 names and the full
layer-2 names, so the client keeps working if the polygon layer is repopulated
in the future (set ``parcel_layer=2`` in that case).
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
        parcel_layer: int = 1,
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
        cleaned_address = sanitize_arcgis_literal(address)
        if not cleaned_address:
            return None

        # The address-points layer matches on ADDRESS; the legacy polygon
        # layer matches on situs. ADDRESS exists only on layer 1, so for the
        # default layer we always query ADDRESS.
        match_field = "ADDRESS" if self.parcel_layer == 1 else "situs"
        params = {
            "where": f"{match_field} LIKE '%{cleaned_address.upper()}%'",
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
        """Map raw ArcGIS attributes to a stable parcel record.

        Accepts both the layer-1 address-points schema (truncated 10-character
        field names) and the layer-2 polygon schema (full field names). Fields
        that exist on neither layer (land/improvement/total value, acreage)
        are no longer returned; they were previously mapped from field names
        that do not exist on the live layers.
        """

        def pick(*names: str) -> Any:
            for name in names:
                value = attributes.get(name)
                if value not in (None, "", " "):
                    return value
            return ""

        return {
            "parcel_id": pick("PIN", "pid"),
            "situs_address": pick("ADDRESS", "situs"),
            "owner_name": pick("ownerName", ""),
            "owner_address": pick("ownerAddre", "ownerAddress"),
            "improvement_area": pick("imprvMainA", "imprvMainArea"),
            "year_built": pick("imprvActua", "imprvActualYearBuilt"),
            "subdivision": pick("SUB_NAME", ""),
            "legal_description": pick("legalDescr", "legalDescription"),
            "lot": pick("lot_1", "Lot"),
            "block": pick("block_1", "Block"),
            "tract": pick("tract_1", "Tract"),
            "city": pick("CITY", ""),
            "state": pick("ST", ""),
            "zip": pick("ZIPCODE", ""),
            "county": pick("COUNTY", ""),
        }


def sanitize_arcgis_literal(value: str) -> str:
    """Sanitize text used inside a simple ArcGIS SQL LIKE literal."""
    return value.strip().replace("'", "''")
