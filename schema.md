# Database schema

Run Log has four tables. Diagram first, then each table in plain English.

```
users 1 ──< routes 1 ──< runs        (a run's route is optional)
users 1 ──< runs
users >──< runs   through   stars    (junction table, many-to-many)
```

## users

One row per account.

| Column | Type | Notes |
|---|---|---|
| id | integer | primary key |
| email | text | unique, required |
| password_hash | text | required (hashed with Werkzeug, never the raw password) |
| created_at | date/time | |

## routes

The places a user usually runs. Belongs to one user.

| Column | Type | Notes |
|---|---|---|
| id | integer | primary key |
| user_id | integer | → users.id, required |
| name | text | required |
| distance_km | number (float) | optional usual distance |
| surface | text | optional: road / trail / track / treadmill |

## runs

One row per run. Belongs to one user, and optionally to one of that user's routes.

| Column | Type | Notes |
|---|---|---|
| id | integer | primary key |
| user_id | integer | → users.id, required |
| route_id | integer | → routes.id, optional (removing a route keeps its runs) |
| run_at | date/time | required, Pacific time |
| distance_km | number (float) | required, more than 0 |
| duration_sec | integer | required, typed as mm:ss or h:mm:ss |
| effort | integer | optional, 1 to 5 |
| notes | text | optional |
| created_at | date/time | |

Pace is **not** a column. It is calculated as `duration_sec / distance_km` whenever it is shown, so it can never disagree with the distance and time.

## stars

The junction table between users and runs. Each row means "this user starred this run". One table for everyone.

| Column | Type | Notes |
|---|---|---|
| id | integer | primary key |
| user_id | integer | → users.id, required |
| run_id | integer | → runs.id, required |
| created_at | date/time | |

A unique constraint on (user_id, run_id) stops the same run being starred twice by the same user. Deleting a run deletes its stars.

## How the tables relate

- users → routes: one-to-many
- users → runs: one-to-many
- routes → runs: one-to-many (a run may have no route)
- users ↔ runs through stars: many-to-many

## Compared with PLAN.md section 3

The agent built the same four tables with the same columns and types as the plan. Two details were added that the plan didn't spell out: removing a route sets its runs' route_id to empty instead of deleting the runs, and deleting a run also deletes its stars. Duration is stored as whole seconds, which the plan described as "number"; the app converts to and from "mm:ss" on the forms.
