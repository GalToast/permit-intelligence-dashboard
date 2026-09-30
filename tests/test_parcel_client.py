import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from parcel_client import PublicParcelClient, sanitize_arcgis_literal


LAYER1_ATTRIBUTES = {
    "PIN": 62381,
    "ADDRESS": "102 LAKESIDE DR",
    "CITY": "CONROE",
    "ST": "TX",
    "ZIPCODE": "77356",
    "COUNTY": "MONTGOMERY",
    "SUB_NAME": "APRIL SOUND",
    "ownerName": "WATTS, THERESA M & RUSSELL D WATTS",
    "ownerAddre": "102 LAKESIDE DR\nMONTGOMERY, TX 77356",
    "imprvActua": 2001,
    "imprvMainA": 2227.0,
    "legalDescr": "April Sound 04, Lot 1",
    "lot_1": "1",
    "block_1": "6",
    "tract_1": " ",
}

LAYER2_ATTRIBUTES = {
    "PIN": 12345,
    "situs": "500 ELM AVE",
    "ownerName": "SAMPLE OWNER",
    "ownerAddress": "500 ELM AVE, CONROE TX 77301",
    "imprvMainArea": 1500,
    "imprvActualYearBuilt": 1999,
    "legalDescription": "LOT 1 BLOCK A",
    "Lot": "1",
    "Block": 2,
    "Tract": "T1",
}


class ParcelClientTests(unittest.TestCase):
    def test_sanitize_arcgis_literal_escapes_single_quotes(self):
        self.assertEqual(sanitize_arcgis_literal("  O'Connor Rd  "), "O''Connor Rd")

    def test_format_parcel_maps_layer1_address_points_schema(self):
        parcel = PublicParcelClient._format_parcel(LAYER1_ATTRIBUTES)
        self.assertEqual(parcel["parcel_id"], 62381)
        self.assertEqual(parcel["situs_address"], "102 LAKESIDE DR")
        self.assertEqual(parcel["owner_name"], "WATTS, THERESA M & RUSSELL D WATTS")
        self.assertEqual(parcel["owner_address"], "102 LAKESIDE DR\nMONTGOMERY, TX 77356")
        self.assertEqual(parcel["improvement_area"], 2227.0)
        self.assertEqual(parcel["year_built"], 2001)
        self.assertEqual(parcel["subdivision"], "APRIL SOUND")
        self.assertEqual(parcel["legal_description"], "April Sound 04, Lot 1")
        self.assertEqual(parcel["lot"], "1")
        self.assertEqual(parcel["block"], "6")
        self.assertEqual(parcel["city"], "CONROE")
        self.assertEqual(parcel["zip"], "77356")
        self.assertNotIn("land_value", parcel)

    def test_format_parcel_falls_back_to_layer2_polygon_schema(self):
        parcel = PublicParcelClient._format_parcel(LAYER2_ATTRIBUTES)
        self.assertEqual(parcel["parcel_id"], 12345)
        self.assertEqual(parcel["situs_address"], "500 ELM AVE")
        self.assertEqual(parcel["owner_address"], "500 ELM AVE, CONROE TX 77301")
        self.assertEqual(parcel["improvement_area"], 1500)
        self.assertEqual(parcel["year_built"], 1999)
        self.assertEqual(parcel["subdivision"], "")
        self.assertEqual(parcel["legal_description"], "LOT 1 BLOCK A")

    def test_format_parcel_handles_empty_attributes(self):
        parcel = PublicParcelClient._format_parcel({})
        for value in parcel.values():
            self.assertEqual(value, "")

    def test_query_by_address_queries_address_field_on_default_layer(self):
        client = PublicParcelClient()
        with patch.object(client.session, "get") as mock_get:
            mock_get.return_value.json.return_value = {"features": [{"attributes": LAYER1_ATTRIBUTES}]}
            mock_get.return_value.raise_for_status.return_value = None
            parcel = client.query_by_address("102 lakeside dr")
        self.assertIsNotNone(parcel)
        self.assertEqual(parcel["parcel_id"], 62381)
        params = mock_get.call_args.kwargs["params"]
        self.assertIn("ADDRESS LIKE '%102 LAKESIDE DR%'", params["where"])
        self.assertIn("/1/query", mock_get.call_args.args[0])

    def test_query_by_address_returns_none_on_network_failure(self):
        client = PublicParcelClient()
        with patch.object(client.session, "get", side_effect=requests.RequestException("boom")):
            self.assertIsNone(client.query_by_address("102 LAKESIDE DR"))

    def test_query_by_address_returns_none_for_blank_address(self):
        client = PublicParcelClient()
        with patch.object(client.session, "get") as mock_get:
            self.assertIsNone(client.query_by_address("   "))
            mock_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
