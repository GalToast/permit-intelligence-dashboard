import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dashboard import esc, render_dashboard, render_row, score_label, to_float, to_int


class ToFloatTests(unittest.TestCase):
    def test_to_float_handles_numeric_and_common_strings(self):
        self.assertEqual(to_float(425000), 425000)
        self.assertEqual(to_float("425000"), 425000)
        self.assertEqual(to_float("$425,000"), 425000)

    def test_to_float_returns_zero_for_malformed_input(self):
        for bad in ("not listed", "$abc", "", "   ", None, "TBD", "--"):
            self.assertEqual(to_float(bad), 0.0, f"input: {bad!r}")

    def test_to_int_returns_zero_for_malformed_input(self):
        self.assertEqual(to_int("85"), 85)
        self.assertEqual(to_int(85.9), 85)
        self.assertEqual(to_int("not listed"), 0)
        self.assertEqual(to_int(None), 0)


class ScoreLabelTests(unittest.TestCase):
    def test_score_label_boundaries(self):
        self.assertEqual(score_label(100), "High")
        self.assertEqual(score_label(80), "High")
        self.assertEqual(score_label(79), "Medium")
        self.assertEqual(score_label(50), "Medium")
        self.assertEqual(score_label(49), "Low")


class RenderRowTests(unittest.TestCase):
    def _record(self, **overrides):
        record = {
            "permit_number": "B-1",
            "permit_type": "Commercial Building",
            "location": "100 SAMPLE RD",
            "status": "Pending",
            "estimated_cost_numeric": 100000,
            "opportunity_score": 80,
            "contractor_company": "Sample Co",
        }
        record.update(overrides)
        return record

    def test_render_row_handles_string_and_malformed_score(self):
        self.assertIn("85", render_row(self._record(opportunity_score="85")))
        self.assertIn(">0<", render_row(self._record(opportunity_score="not a score")))
        self.assertIn(">0<", render_row(self._record(opportunity_score=None)))

    def test_render_row_handles_malformed_cost(self):
        self.assertIn("$0", render_row(self._record(estimated_cost_numeric="not listed")))
        self.assertIn("$100,000", render_row(self._record(estimated_cost_numeric="$100,000")))
        self.assertIn("$0", render_row(self._record(estimated_cost_numeric=None)))

    def test_render_row_escapes_html(self):
        row = render_row(self._record(contractor_company='<script>alert("x")</script>'))
        self.assertNotIn("<script>", row)
        self.assertIn("&lt;script&gt;", row)


class RenderDashboardTests(unittest.TestCase):
    def test_render_dashboard_tolerates_malformed_numeric_strings(self):
        records = [
            {"permit_number": "B-1", "opportunity_score": "85", "estimated_cost_numeric": "$250,000"},
            {"permit_number": "B-2", "opportunity_score": "not listed", "estimated_cost_numeric": "TBD"},
            {"permit_number": "B-3", "opportunity_score": None, "estimated_cost_numeric": None},
        ]
        page = render_dashboard(records)
        self.assertIn("Permit Intelligence Dashboard", page)
        self.assertIn("$250,000", page)  # only the valid record contributes

    def test_esc_handles_none_and_malicious_input(self):
        self.assertEqual(esc(None), "")
        self.assertEqual(esc("<b>&</b>"), "&lt;b&gt;&amp;&lt;/b&gt;")


if __name__ == "__main__":
    unittest.main()
