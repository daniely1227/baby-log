# Prompt log: dashboard (feature 7)

## Prompt

> Build feature 7 from PLAN.md on the branch feature/dashboard. Add a Dashboard page with three summary cards: km in the last 7 days, runs in the last 30 days, and longest run (with its date). Add a bar chart of km per week for the last 8 weeks with Chart.js, black bars to match the design. Weeks run Monday to Sunday. Put the math in its own file so it can be tested without the web pages, and use Pacific time for "now".

## Agent response (summary)

Created stats.py with week_start(), km_in_last_days(), runs_in_last_days(), longest_run(), weekly_km() and dashboard_stats(). The /dashboard route loads only the logged-in user's runs. The chart loads Chart.js 4.4.1 from cdnjs. With no runs the longest-run card shows "—" instead of crashing.

## Checked

With runs of 5 km (1 day ago), 3.5 km (3 days ago), 10 km (6 days ago) and 20 km (10 days ago): km in the last 7 days = 18.5 km, runs in the last 30 days = 4, longest = 20.0 km, and the chart put 18.5 km in the current week and 20 km in the week before.
