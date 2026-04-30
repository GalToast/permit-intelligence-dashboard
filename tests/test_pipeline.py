import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pipeline import PermitIntelligencePipeline, extract_street_address, parse_money, write_outputs


class PipelineTests(unittest.TestCase):
    def test_parse_money_handles_common_formats(self):
        self.assertEqual(parse_money("$250,000"), 250000)
        self.assertEqual(parse_money("75000"), 75000)
        self.assertEqual(parse_money(""), 0)
        self.assertEqual(parse_money("not listed"), 0)

    def test_extract_street_address_removes_city_state_zip(self):
        self.assertEqual(extract_street_address("100 SAMPLE RD CONROE, TX 77301"), "100 SAMPLE RD")

    def test_scoring_rewards_commercial_value_status_and_contact(self):
        pipeline = PermitIntelligencePipeline(min_cost=50000)
        scored = pipeline._score(
            {
                "permit_type": "Commercial Building",
                "project_type": "New Construction",
                "status": "Pending",
                "estimated_cost": "$250,000",
                "contractor_email": "sample@example.com",
            }
        )
        self.assertEqual(scored["estimated_cost_numeric"], 250000)
        self.assertIs(scored["is_commercial"], True)
        self.assertEqual(scored["opportunity_score"], 90)

    def test_write_outputs_can_generate_dashboard(self):
        with self.subTest("outputs"):
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                records = [
                    {
                        "permit_number": "B-1",
                        "permit_type": "Commercial Building",
                        "location": "100 SAMPLE RD",
                        "status": "Pending",
                        "estimated_cost_numeric": 100000,
                        "opportunity_score": 80,
                        "is_commercial": True,
                    }
                ]
                write_outputs(
                    records,
                    json_path=str(tmp_path / "records.json"),
                    csv_path=str(tmp_path / "records.csv"),
                    dashboard_path=str(tmp_path / "dashboard.html"),
                )
                self.assertTrue((tmp_path / "records.json").exists())
                self.assertTrue((tmp_path / "records.csv").exists())
                dashboard = (tmp_path / "dashboard.html").read_text(encoding="utf-8")
                self.assertIn("Permit Intelligence Dashboard", dashboard)


if __name__ == "__main__":
    unittest.main()
