# Prompt log: create / read / update / delete runs (feature 3)

## Prompt

> Build feature 3 from PLAN.md on the branch feature/crud. I need: a Runs page listing my runs newest first (distance big, then time, route and date), a "Log a run" form (date and time, route from my routes, distance in km, time as mm:ss or h:mm:ss, effort 1 to 5, notes), a detail page for one run, an edit form, and delete with an "Are you sure?" confirmation page (not a browser pop-up, so it is clear on a phone). When I pick a route, fill in its usual distance if the distance box is empty. A user must never be able to open, edit or delete someone else's run.

## Agent response (summary)

Added /runs, /runs/new, /runs/<id>, /runs/<id>/edit and /runs/<id>/delete, plus get_own_run() which returns 404 unless the run belongs to the logged-in user. The time box accepts "31:12" or "1:02:05" and is stored as seconds. A shared macro draws the run rows. For now, a form that can't be read shows a single "Please check the form." message; specific messages come in feature 4.

## Checked

Logged 5.2 km in 31:12 on "Marina loop", opened it ("5.20 km in 31:12"), edited it to 10 km in 1:02:05 with no route, deleted it through the "Are you sure?" page. A second account got 404 on the first account's run and its edit page.
