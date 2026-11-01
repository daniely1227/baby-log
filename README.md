# Run Log

A small web app for logging my jogging runs in km. Each run has a date, distance, time, optional route, effort and notes. The app works out the pace, shows weekly totals and a pace trend, and keeps my habit going with a weekly streak.

**Live app:** LIVE_URL_PLACEHOLDER

Built for the Intro to Code solo app assignment (Haas, Fall 2026). See [PLAN.md](PLAN.md) for the plan and [schema.md](schema.md) for the database.

## What it does

- **Accounts.** Sign up, log in and log out. Every user only sees their own routes and runs.
- **Routes.** Save the loops you run most, with a usual distance and surface.
- **Runs.** Add, view, edit and delete runs (delete asks "Are you sure?" first). Time is typed as `32:15` or `1:05:30`.
- **Validation.** Friendly messages for a missing date, a distance of 0, a time in the wrong format, and similar mistakes.
- **Stars.** Star any run and see all starred runs on one page.
- **Find.** Search notes, filter by route or month, sort by newest, oldest, longest or fastest pace.
- **Dashboard.** km in the last 7 days, runs in the last 30 days, longest run, average and best pace, a weekly km bar chart and a pace line chart.
- **Pace.** Calculated for every run (min per km), never typed in.
- **Same as last time.** One tap on the home page logs today's run on a saved route with the same distance and time as last time.
- **Last run and streak.** "Last run 2 days ago" and how many weeks in a row you've run.
- **CSV export.** Download every run as a spreadsheet.

## How it's built

| Part | Tool |
|---|---|
| Language / framework | Python 3.12, Flask |
| Database | PostgreSQL on Render (SQLite locally and in tests), via Flask-SQLAlchemy |
| Login | Flask-Login, passwords hashed with Werkzeug |
| Charts | Chart.js 4.4.1 from cdnjs |
| Tests | pytest |
| Hosting | Render free web service + free PostgreSQL, deployed from `main` (see `render.yaml`) |
| Coding agent | Claude Code, one feature per branch and pull request; prompts are in `prompts/` |

```
app.py        routes (pages) and form handling
models.py     tables: User, Route, Run, Star, plus time and pace helpers
stats.py      dashboard and streak math (kept separate so it can be tested)
templates/    HTML pages (Jinja)
static/       style.css
tests/        the two required tests
prompts/      prompt log for every feature
```

## Run it on your computer

```bash
git clone https://github.com/daniely1227/run-log.git
cd run-log
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # then open http://127.0.0.1:5000
```

Without a `DATABASE_URL`, the app uses a local SQLite file, so no database setup is needed.

## Run the tests

```bash
python -m pytest -q
```

- `tests/test_data_isolation.py`: User B can't see, open, edit, delete or star User A's run.
- `tests/test_dashboard.py`: "km in the last 7 days" shows 18.5 km for runs of 5, 3.5 and 10 km, ignoring a 20 km run from 10 days ago.

## Deploy

Render reads `render.yaml`, creates a free web service and a free PostgreSQL database, and redeploys whenever a pull request is merged into `main`.
