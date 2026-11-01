# Prompt log for the PostgreSQL start-up fix

## Prompt

> Double-check everything you built before I deploy it, as thoroughly as you can.

## Agent response (summary)

The agent ran the app the way Render will run it, with a real PostgreSQL database instead of SQLite, a fresh Python 3.12 environment built from requirements.txt, and gunicorn. The app did not start. Every gunicorn worker crashed with `ModuleNotFoundError: No module named 'psycopg'`. requirements.txt did not pin SQLAlchemy, so pip installed SQLAlchemy 2.1, and for an address that starts with postgresql:// that version looks for the newer psycopg driver instead of psycopg2, which is the one we install. The tests never caught it because they use SQLite.

Fixes
- `database_url()` now rewrites postgres:// and postgresql:// to postgresql+psycopg2://, so the driver is named explicitly.
- requirements.txt pins SQLAlchemy and Werkzeug to the versions that were tested, and adds tzdata so Pacific time works even on a server without time zone files.
- On a brand-new database, two gunicorn workers could both try to create the tables at the same moment, and one of them crashed (`duplicate key value violates unique constraint "pg_type_typname_nsp_index"`, seen once in six cold starts). Table creation now waits a second and tries again.
- Added `tests/test_database_url.py` so the address rewrite can't silently break again.

## Checked

Fresh clone, Python 3.12, PostgreSQL 16. Before the fix, 5 of 5 cold starts crashed. After it, 15 of 15 cold starts with 4 workers came up and served the login page. The full click-through (sign up, routes, add, edit, delete, validation, stars, search, filters, sorts, one-tap repeat, streak, dashboard charts, CSV, and a second user trying to reach the first user's runs) passed on PostgreSQL.
