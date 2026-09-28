# Architecture

## Overview

The portal is a single Flask application running on port 8080. It uses SQLite in the local `instance/` directory, so it has no hosted database or third-party dependency at runtime.

## Components

- **Flask routes** render the gallery, project details, submission form, organizer dashboard, and JSON/CSV endpoints.
- **SQLite** stores the project gallery and locally created submissions.
- **fixtures.json** is read at startup and seeds the initial projects, teams, tracks, and scores.
- **Docker Compose** starts one container and preserves the SQLite database in a named volume.

## Access control

The application maps fixed, seeded session cookies to roles. This lets the DOGFOOD checker test the backend directly. `/api/judge/scores` always uses the identity in the cookie; it refuses an attempt to request another judge's records. `/api/export.csv` requires an organizer session.

## Local operation

`docker compose up --build` builds the application image and serves it at `http://localhost:8080`.
