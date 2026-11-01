# Run Log Plan

## 1. Pitch

I'm building **Run Log** because I run 3 to 5 times a week and I'm training to run 10 km in under 50 minutes, which means holding a pace of 5:00 per km. I'm still a beginner, so I want one simple place where I log each run's distance and time, see my pace, and check week by week whether I'm getting closer to that goal.

I'll use it after every run, 3 to 5 times a week, and look at the dashboard once a week.

## 2. Features (user stories, in build order)

**Spine features**

1. **Sign up and login.** As a runner, I want to create my own account with an email and password and log in and out, so that only I can see my runs.
2. **Data model and routes.** As a runner, I want to save the routes I usually run (name, distance in km, surface), so that each run can be linked to a route.
3. **Create / read / update / delete runs.** As a runner, I want to add a run (date and time, distance in km, duration, route, effort 1 to 5, notes), see the list, open one run's detail page, edit it, and delete it after an "are you sure?" confirmation, so that my log stays accurate.
4. **Validation.** As a runner, I want the app to stop me from saving a run without a date, a distance above 0 km or a duration in a valid format like 32:15, with a friendly message, so that I don't save broken records.
5. **Stars.** As a runner, I want to star a run (for example a personal best or a run that felt great) and see all starred runs on one page, so that I can find my best runs quickly.
6. **Find things.** As a runner, I want to filter runs by route and by month, search the notes, and sort by newest, oldest or longest distance, so that I can answer "when did I last run the Berkeley Marina loop?"
7. **Dashboard.** As a runner, I want a chart of km per week for the last 8 weeks and summary stats (km in the last 7 days, runs in the last 30 days, longest run), so that I can see whether I'm running more or less.

**My features**

8. **Pace.** As a runner, I want the app to calculate my pace (minutes per km) for every run, show my average and best pace on the dashboard with a pace trend chart, and let me sort runs by fastest pace, so that I can see whether I'm getting faster.
9. **One-tap repeat run.** As a runner, I want a "Same as last time" button for each saved route that logs today's run with that route's last distance and time, so that logging my usual loop takes one tap (and I can edit it after).
10. **Last run and streak.** As a runner, I want the home screen to show "Last run 2 days ago" and how many weeks in a row I've run, so that I keep the habit going.
11. **CSV export.** As a runner, I want to download all my runs as a CSV file, so that I can open them in Excel.

## 3. Database

Four tables. Types are text, number, date/time or true/false.

**users**

| Column | Type | Notes |
|---|---|---|
| id | number | primary key |
| email | text | unique, required |
| password_hash | text | required, never the raw password |
| created_at | date/time | |

**routes**

| Column | Type | Notes |
|---|---|---|
| id | number | primary key |
| user_id | number | references users.id |
| name | text | required, e.g. "Berkeley Marina loop" |
| distance_km | number | optional usual distance |
| surface | text | optional, road / trail / track / treadmill |

**runs**

| Column | Type | Notes |
|---|---|---|
| id | number | primary key |
| user_id | number | references users.id |
| route_id | number | optional, references routes.id |
| run_at | date/time | required |
| distance_km | number | required, more than 0 |
| duration_sec | number | required, stored in seconds, typed as mm:ss or h:mm:ss |
| effort | number | optional, 1 (easy) to 5 (all out) |
| notes | text | optional |
| created_at | date/time | |

Pace is not stored. It is calculated as duration_sec / distance_km, so it can never disagree with the distance and time.

**stars** (junction table)

| Column | Type | Notes |
|---|---|---|
| id | number | primary key |
| user_id | number | references users.id |
| run_id | number | references runs.id |
| created_at | date/time | |

One user + run pair can only be starred once.

**How the tables connect**

```
users 1 ──< routes 1 ──< runs
users 1 ──< runs
users >──< runs   (many-to-many through stars)
```

- One user has many routes and many runs (one-to-many).
- One route has many runs (one-to-many). A run doesn't have to have a route.
- Users and runs are many-to-many through **stars**. One stars table for everyone, each row says "this user starred this run".

## 4. Tests

1. **Data isolation.** Given User A has logged one run, when User B signs up, opens the runs list and tries to open User A's run by its URL, then User B sees an empty list and gets a "not found" page for User A's run.
2. **Dashboard stat.** Given a user logged runs of 5 km, 3.5 km and 10 km in the last 7 days and a 20 km run 10 days ago, when they open the dashboard, then "km in the last 7 days" shows 18.5 km.

## 5. Technologies

- **Claude Code as the coding agent.** It can write the code, run the tests and open the GitHub issues, branches and pull requests for each feature.
- **Python with Flask for the app.** Flask is small and readable, so I can follow how a request turns into a page.
- **PostgreSQL on Render for the database (SQLite in memory for tests).** A hosted database keeps my runs when the app restarts, and SQLAlchemy lets the same code run on both.
- **Flask-Login with hashed passwords (Werkzeug) for sign up and login.** The standard, simple way to keep each user logged in without storing plain passwords.
- **Render free web service for hosting, deployed from GitHub.** It redeploys automatically every time a pull request is merged into main, so the live URL stays current.
- **Chart.js for charts, pytest for tests and gunicorn as the web server.** Each is the common default for its job.

## 6. Design

Clean monochrome, with a white background, black text, gray borders, one black accent for buttons and no decoration. Big numbers for distance and pace, and a phone-first layout because I log right after a run. Inspiration is the Nike Run Club summary screen (one big number per card) and the Apple Health app.

## 7. Risks and cuts

- **Least sure I can build.** The weekly streak, because "weeks in a row" depends on where a week starts and on weeks with no runs, which is easy to get off by one. I'll define weeks as Monday to Sunday.
- **First to cut if I run out of time.** CSV export, because I don't need it week to week.
- **Hosting risk.** Render's free database expires after a limited time, which is fine through the Nov 4 demo but would need an upgrade for long-term use.
