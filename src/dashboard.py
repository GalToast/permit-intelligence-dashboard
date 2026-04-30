"""Generate a static review dashboard from scored permit records."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def score_label(score: int) -> str:
    if score >= 80:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def render_dashboard(records: list[dict[str, Any]]) -> str:
    total_value = sum(float(record.get("estimated_cost_numeric") or 0) for record in records)
    commercial = sum(1 for record in records if record.get("is_commercial"))
    with_contact = sum(1 for record in records if record.get("contractor_phone") or record.get("contractor_email"))

    rows = "\n".join(render_row(record) for record in records)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Permit Intelligence Dashboard</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #17202a; background: #f6f7f9; }}
    header {{ padding: 32px; background: #17202a; color: white; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 20px 0; }}
    .stat, table {{ background: white; border: 1px solid #dde3ea; border-radius: 8px; }}
    .stat {{ padding: 16px; }}
    .stat strong {{ display: block; font-size: 24px; }}
    table {{ width: 100%; border-collapse: collapse; overflow: hidden; }}
    th, td {{ padding: 12px; border-bottom: 1px solid #edf1f5; text-align: left; vertical-align: top; }}
    th {{ background: #eef3f8; font-size: 13px; text-transform: uppercase; letter-spacing: .04em; }}
    .score {{ font-weight: 700; }}
    .High {{ color: #0f7a3f; }}
    .Medium {{ color: #9a6500; }}
    .Low {{ color: #6b7280; }}
    @media (max-width: 760px) {{ .stats {{ grid-template-columns: 1fr 1fr; }} table {{ font-size: 13px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Permit Intelligence Dashboard</h1>
    <p>Public-record permit opportunities scored for human review.</p>
  </header>
  <main>
    <section class="stats">
      <div class="stat"><span>Total records</span><strong>{len(records)}</strong></div>
      <div class="stat"><span>Commercial</span><strong>{commercial}</strong></div>
      <div class="stat"><span>With contact fields</span><strong>{with_contact}</strong></div>
      <div class="stat"><span>Total project value</span><strong>${total_value:,.0f}</strong></div>
    </section>
    <table>
      <thead>
        <tr>
          <th>Score</th>
          <th>Permit</th>
          <th>Type</th>
          <th>Project</th>
          <th>Contractor</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </main>
</body>
</html>"""


def render_row(record: dict[str, Any]) -> str:
    score = int(record.get("opportunity_score") or 0)
    label = score_label(score)
    cost = float(record.get("estimated_cost_numeric") or 0)
    contractor = record.get("contractor_company") or record.get("contractor_name") or "Not listed"
    return f"""<tr>
  <td class="score {label}">{score}<br>{label}</td>
  <td>{esc(record.get("permit_number", ""))}</td>
  <td>{esc(record.get("permit_type", ""))}</td>
  <td>{esc(record.get("location", ""))}<br>${cost:,.0f}</td>
  <td>{esc(contractor)}</td>
  <td>{esc(record.get("status", ""))}</td>
</tr>"""


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static permit dashboard.")
    parser.add_argument("--input", default="filtered_opportunities.json")
    parser.add_argument("--output", default="dashboard.html")
    args = parser.parse_args()

    records = json.loads(Path(args.input).read_text(encoding="utf-8"))
    Path(args.output).write_text(render_dashboard(records), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
