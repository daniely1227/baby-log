# Prompt log for test 2, dashboard stat

## Prompt

> On the branch test/dashboard-stat, write a pytest test for test 2 in PLAN.md section 4. Log runs of 5 km (1 day ago), 3.5 km (3 days ago), 10 km (6 days ago) and 20 km (10 days ago), open /dashboard as that user, and check that "km in the last 7 days" shows exactly "18.5 km". The 20 km run must not count.
>
> Then prove it: temporarily break km_in_last_days() in stats.py, run the test and capture it failing, undo the break, and capture it passing.

## Agent response (summary)

Added tests/test_dashboard.py. It creates the four runs relative to the current Pacific time, loads the dashboard page and reads the number from the element with id "stat-km-7d". For the red run the 7-day window was removed, so all runs were added up (38.5 km), and the test failed with "assert '38.5 km' == '18.5 km'". After undoing it, the test passed.

## Screenshots

- docs/screenshots/dashboard-red.png
- docs/screenshots/dashboard-green.png
