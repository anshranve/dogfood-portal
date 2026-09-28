# Data model

## Imported data

The official fixture file contains an event, tracks, judges, teams, projects, and scores. IDs remain strings and timestamps stay in ISO 8601 UTC form.

## Local table: projects

| Field | Purpose |
| --- | --- |
| `id` | Stable fixture or locally generated project identifier |
| `title` | Project name |
| `summary` | Public short description |
| `repo_url` | Source repository link |
| `track` | Human-readable track name |
| `team` | Human-readable team name |
| `submitted_at` | ISO 8601 submission timestamp |
| `is_fixture` | Distinguishes seeded and local entries |

## Import and export

At first launch the application imports `fixtures.json` from the repository root. An organizer can retrieve the project dataset from `/api/export.csv`. The CSV format is intentionally simple so it can be opened in a spreadsheet or imported into a future system.
