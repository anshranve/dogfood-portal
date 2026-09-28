# DOGFOOD Portal

A local-first submission and judging portal built with Flask and SQLite.

## Run locally

```powershell
.\.venv\Scripts\python.exe app.py
```

Then open http://127.0.0.1:8080/projects in your browser.

To run with Docker:

```powershell
docker compose up --build
```

The app reads the official `fixtures.json` when it is present beside `app.py`. Without that file it uses one small sample project so the first screen can still be explored. Download the official fixture file from https://dogfoodhack.com/spec/fixtures.json before preparing the hackathon submission.

## Current scope

- Public searchable project gallery
- Individual project detail page
- Project submission form with deadline enforcement
- SQLite storage for local submissions
- Judge score API with backend-enforced judge isolation
- Organizer-only CSV export at `/api/export.csv`

The fixed checker sessions are listed in `.dogfood.toml`. The acceptance suite sends them directly as cookies. The organizer dashboard is available at `/organizer` when the organizer session cookie is present.
