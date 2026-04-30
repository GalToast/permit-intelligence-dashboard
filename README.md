# Permit Intelligence Dashboard

Public-record data pipeline for turning building permits into reviewable business opportunities.

This project is a sanitized portfolio version of a local permit-intelligence workflow. It combines public permit search, parcel enrichment, scoring, CSV/JSON exports, and a static dashboard concept for operator review. The point is not spam automation. The point is practical data work: collect public records, enrich them, score them, and give a human a clean review surface.

## What It Demonstrates

- Browser automation against public permit portals
- Public ArcGIS REST API enrichment
- Lead/opportunity scoring from noisy records
- Static dashboard generation
- Rate limiting and polite scraping defaults
- Separation between raw public data and review-ready outputs
- Business automation thinking without hiding the human review step

## Architecture

```text
public permit portal
  -> permit scraper
  -> parcel/property enrichment
  -> scoring + filtering
  -> CSV / JSON exports
  -> static dashboard for review
```

## Repository Layout

| Path | Purpose |
| --- | --- |
| `src/permit_scraper.py` | Playwright scraper for public OpenGov-style permit search |
| `src/parcel_client.py` | Public ArcGIS REST API parcel lookup client |
| `src/pipeline.py` | End-to-end scrape, enrich, score, and export pipeline |
| `src/dashboard.py` | Static HTML dashboard generator |
| `examples/sample_permits.json` | Synthetic sample data for local dashboard testing |
| `docs/portfolio-case-study.md` | Recruiter-facing explanation of the project |

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Generate a dashboard from the synthetic sample:

```bash
python src/dashboard.py --input examples/sample_permits.json --output dashboard.html
```

Run the public-record pipeline:

```bash
python src/pipeline.py --max-permits 10 --min-cost 50000 --headless
```

Write JSON, CSV, and a static dashboard in one pass:

```bash
python src/pipeline.py --max-permits 10 --min-cost 50000 --headless --dashboard dashboard.html
```

Run focused tests:

```bash
python -m unittest discover -s tests
```

## Configuration

The default implementation targets the City of Conroe public OpenGov and ArcGIS endpoints because those were the original research surface. The code is intentionally written so another OpenGov-style city portal can be substituted with a different base URL.

No API keys are required for the included public endpoints.

Live scraping is portal-layout dependent. The deterministic parts of the repo, including money parsing, address extraction, scoring, export, and dashboard rendering, are covered by focused tests.

## Ethics

Use this kind of workflow carefully:

- Respect robots.txt, portal terms, rate limits, and public-data restrictions.
- Do not scrape behind logins or access controls.
- Do not publish raw personal contact exports.
- Treat generated opportunity lists as review queues, not automated spam targets.
- Keep outreach compliant with applicable law and platform rules.

## Hiring Signal

For AI-adjacent and automation roles, this repo shows a practical pattern: use AI and automation around public data, but keep the output bounded, inspectable, and reviewable by a human operator.
