# Prompt log for stars (feature 5)

## Prompt

> Build feature 5 from PLAN.md on the branch feature/stars. Add a stars table that is a junction table between users and runs (id, user_id, run_id, created_at), one row per "this user starred this run", and the same user can't star the same run twice. Put a ☆ / ★ toggle on every run in the list and on the detail page, and add a "Starred" page in the menu. Starring someone else's run must not be possible, and deleting a run should remove its stars.

## Agent response (summary)

Added the Star model with a unique (user_id, run_id) constraint, a POST /runs/<id>/star toggle that reuses get_own_run() so other users get 404, and a /starred page. The run-row macro now includes the star button. Deleting a run cascades to its stars. After starring, the app only redirects to paths inside the app, so a crafted "next" value like //evil.com goes to the run's own page instead.

## Checked

Starred the 10 km "PB" run (it showed on Starred, the 5 km run did not), starred then unstarred the 5 km run, deleted a starred run and confirmed 0 stars remain, and a second account got 404 trying to star the first account's run. A "next" of //evil.com redirected to /runs/1.
