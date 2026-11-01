# Prompt log: last run and weekly streak (my feature 10)

## Prompt

> Build my feature 10 from PLAN.md on the branch feature/streak. At the top of the home page show two cards: "Last run" (Today, Yesterday, or "N days ago") and "Weekly streak" (how many weeks in a row I ran at least once). Weeks are Monday to Sunday. If I haven't run yet this week, the streak shouldn't drop to 0, because the week isn't over; count from last week instead. Put the logic in stats.py so it can be tested.

## Agent response (summary)

Added days_since_last_run() and weekly_streak() to stats.py and two highlighted cards on the home page. weekly_streak() collects the Monday of every week that has a run, starts at this week (or last week if this week has no run yet) and counts backwards until it finds a week with no run.

## Checked

Using fixed dates with "now" on Sunday Nov 1: no runs → 0; a run today → 1; runs on Oct 20 and Oct 28 (two weeks in a row) → 2; runs on Oct 14 and Oct 28 (a gap week between) → 1. On Tuesday Nov 3 with no run yet that week, the Oct 20 + Oct 28 streak still shows 2, and days since the Oct 28 run = 6. On the live page, a new account shows "No runs yet" and "0 weeks"; after a run 2 days ago it shows "2 days ago" and "1 week".
