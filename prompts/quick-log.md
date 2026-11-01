# Prompt log for one-tap repeat run (my feature 9)

## Prompt

> Build my feature 9 from PLAN.md on the branch feature/quick-log. On the home page, show one big button per saved route labelled with the route name and the last distance and time on that route ("Marina · 5.2 km · 31:12"). One tap logs a run right now with the same distance, time and effort as my last run on that route, then opens the new run so I can edit it if today was different. If I've never run that route, the button should open the normal form with the route and its usual distance already filled in. Also show my 5 most recent runs on the home page.

## Agent response (summary)

Added POST /routes/<id>/repeat, which copies distance, duration and effort from the most recent run on that route into a new run at the current Pacific time, and falls back to /runs/new?route=<id> (prefilled) when there is no earlier run. The home page now has a "Same as last time" grid and a "Recent runs" list.

## Checked

With no routes the home page points to the Routes page. "Marina" with no runs opened the form with 5.2 km filled in. After logging 5.2 km in 31:12 on Marina, the button read "5.2 km · 31:12" and one tap created a new 5.20 km in 31:12 run. A second account got 404 when posting to the first account's route.
