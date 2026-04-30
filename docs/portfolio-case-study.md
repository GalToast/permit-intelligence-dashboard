# Portfolio Case Study

## Problem

Local service businesses often need to find projects before they become obvious. Public permit records contain useful signals, but the workflow is slow when handled manually:

- search a city portal
- open individual permit records
- copy project details
- look up parcel/property context
- decide which records are worth reviewing
- build a list a human can act on

## System

This project packages that workflow into a small public-data pipeline:

1. Search an OpenGov-style permit portal.
2. Extract permit number, type, status, location, value, and contractor fields.
3. Enrich records with public ArcGIS parcel data when an address is available.
4. Score each record by project value, commercial/residential type, status, and contact fields.
5. Export JSON/CSV and generate a static review dashboard.

## AI-Adjacent Signal

This is the kind of automation that fits AI operations work:

- A human defines the business signal.
- Scripts collect and normalize public records.
- Scoring narrows the review queue.
- A dashboard makes the output inspectable.
- AI can help summarize, classify, or draft next steps after the data has been bounded.

## Evidence Discipline

The public repo uses synthetic sample data. The production pattern should keep raw exports private unless there is a clear legal and ethical reason to publish them.

## What I Would Improve Next

- Add city-portal adapters with explicit capability flags.
- Add a dedupe layer across repeated daily runs.
- Add a review status field for human outcomes.
- Add tests around money parsing, address extraction, and scoring.
- Add optional LLM summarization only after deterministic fields are extracted.
