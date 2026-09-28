"""A small, local-first DOGFOOD portal starter built with Flask and SQLite."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import uuid

from flask import Flask, Response, abort, g, jsonify, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "instance"
DATABASE = DATA_DIR / "portal.sqlite3"
FIXTURES_FILE = BASE_DIR / "fixtures.json"

app = Flask(__name__)
app.config["SECRET_KEY"] = "local-demo-only-change-before-production"

FALLBACK_FIXTURES = {
    "event": {
        "id": "evt_01",
        "name": "Sample Hack 2026",
        "submissions_close": "2026-03-01T18:00:00Z",
    },
    "tracks": [{"id": "trk_01", "name": "Developer tools"}],
    "teams": [{"id": "tm_01", "name": "Sample Team", "members": []}],
    "projects": [
        {
            "id": "prj_01",
            "team": "tm_01",
            "track": "trk_01",
            "title": "Glass Signal",
            "summary": "A sample project from the DOGFOOD fixture set.",
            "repo_url": "https://example.org/repo/01",
            "submitted_at": "2026-02-27T04:08:00Z",
        }
    ],
    "scores": [
        {"judge": "jdg_01", "project": "prj_01", "criteria": {"functionality": 4, "quality": 4}, "comment": "Clear and useful."}
    ],
}

SESSIONS = {
    "org_7f2a": {"role": "organizer", "id": "org_01", "name": "Morgan Lee"},
    "jdg_a_91bc": {"role": "judge", "id": "jdg_01", "name": "Judge A"},
    "jdg_b_44de": {"role": "judge", "id": "jdg_02", "name": "Judge B"},
    "prt_2e88": {"role": "participant", "id": "prt_01", "name": "Participant"},
}


def load_fixtures():
    if FIXTURES_FILE.exists():
        with FIXTURES_FILE.open(encoding="utf-8") as file:
            return json.load(file)
    return FALLBACK_FIXTURES


def parse_utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def current_user():
    return SESSIONS.get(request.cookies.get("session"))


def require_role(*roles):
    user = current_user()
    if user is None or user["role"] not in roles:
        abort(403)
    return user


def get_db():
    if "db" not in g:
        DATA_DIR.mkdir(exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def initialize_database():
    fixtures = load_fixtures()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute(
        """CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            repo_url TEXT NOT NULL,
            track TEXT NOT NULL,
            team TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            is_fixture INTEGER NOT NULL DEFAULT 0
        )"""
    )
    count = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    if count == 0:
        teams = {team["id"]: team["name"] for team in fixtures.get("teams", [])}
        tracks = {track["id"]: track["name"] for track in fixtures.get("tracks", [])}
        for project in fixtures.get("projects", []):
            db.execute(
                """INSERT OR IGNORE INTO projects
                   (id, title, summary, repo_url, track, team, submitted_at, is_fixture)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    project.get("id", str(uuid.uuid4())),
                    project.get("title", "Untitled project"),
                    project.get("summary", ""),
                    project.get("repo_url", ""),
                    tracks.get(project.get("track"), project.get("track", "Unassigned")),
                    teams.get(project.get("team"), project.get("team", "Independent")),
                    project.get("submitted_at", ""),
                ),
            )
        db.commit()
    db.close()


@app.context_processor
def event_context():
    return {"event": load_fixtures().get("event", {}), "current_user": current_user()}


@app.get("/")
def home():
    return redirect(url_for("projects"))


@app.get("/projects")
def projects():
    query = request.args.get("q", "").strip()
    db = get_db()
    if query:
        like = f"%{query}%"
        rows = db.execute(
            """SELECT * FROM projects
               WHERE title LIKE ? OR summary LIKE ? OR track LIKE ? OR team LIKE ?
               ORDER BY title""",
            (like, like, like, like),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM projects ORDER BY title").fetchall()
    return render_template("projects.html", projects=rows, query=query)


@app.get("/projects/<project_id>")
def project_detail(project_id):
    project = get_db().execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    if project is None:
        abort(404)
    return render_template("project_detail.html", project=project)


@app.route("/projects/new", methods=["GET", "POST"])
def submit_project():
    fixtures = load_fixtures()
    closes_at = parse_utc(fixtures["event"]["submissions_close"])
    is_closed = datetime.now(timezone.utc) >= closes_at

    if request.method == "GET":
        return render_template("submit.html", is_closed=is_closed), 200

    if is_closed:
        return render_template("submit.html", is_closed=True), 403

    title = request.form.get("title", "").strip()
    summary = request.form.get("summary", "").strip()
    repo_url = request.form.get("repo_url", "").strip()
    track = request.form.get("track", "Unassigned").strip()
    if not title or not summary or not repo_url:
        return render_template(
            "submit.html", is_closed=False, error="Title, summary, and repository URL are required."
        ), 400

    db = get_db()
    db.execute(
        """INSERT INTO projects
           (id, title, summary, repo_url, track, team, submitted_at, is_fixture)
           VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
        (
            f"local_{uuid.uuid4().hex[:12]}",
            title,
            summary,
            repo_url,
            track or "Unassigned",
            "New team",
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    db.commit()
    return redirect(url_for("projects"))


@app.get("/api/judge/scores")
def judge_scores():
    """Return only the requesting judge's scores; do not trust a query string."""
    judge = require_role("judge")
    requested = request.args.get("judge")
    allowed_alias = "judge_a" if judge["id"] == "jdg_01" else "judge_b"
    if requested and requested not in {judge["id"], allowed_alias}:
        abort(403)
    scores = [score for score in load_fixtures().get("scores", []) if score.get("judge") == judge["id"]]
    return jsonify({"judge": judge["id"], "scores": scores})


@app.get("/api/export.csv")
def export_csv():
    require_role("organizer")
    rows = get_db().execute(
        "SELECT id, title, summary, repo_url, track, team, submitted_at FROM projects ORDER BY title"
    ).fetchall()
    lines = ["id,title,summary,repo_url,track,team,submitted_at"]
    for row in rows:
        values = [str(row[column]).replace('"', '""') for column in row.keys()]
        lines.append(",".join(f'"{value}"' for value in values))
    return Response("\n".join(lines) + "\n", content_type="text/csv; charset=utf-8")


@app.get("/organizer")
def organizer_dashboard():
    require_role("organizer")
    projects = get_db().execute("SELECT * FROM projects ORDER BY submitted_at DESC").fetchall()
    return render_template("organizer.html", projects=projects)


with app.app_context():
    initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
