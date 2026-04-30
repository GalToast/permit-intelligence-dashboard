import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from parcel_client import sanitize_arcgis_literal


class ParcelClientTests(unittest.TestCase):
    def test_sanitize_arcgis_literal_escapes_single_quotes(self):
        self.assertEqual(sanitize_arcgis_literal("  O'Connor Rd  "), "O''Connor Rd")


if __name__ == "__main__":
    unittest.main()
