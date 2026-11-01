# Prompt log: plan

## My decisions (given to the agent as answers in an interview)

- First idea was a baby log, but I don't have a baby yet, so I switched before merging the plan: the app tracks my jogging.
- Distance in km.
- My features: pace (my own addition), one-tap repeat of a usual route, last run and streak, CSV export.
- Design: clean monochrome.
- Hosting: Render.
- Tools: Claude Code builds; I review, merge and deploy.

## Prompt

> Using my answers above, write PLAN.md with all 7 sections from the assignment brief for a running log in km. Make every line specific: list the exact columns for each table, write each feature as a user story in build order, and write both tests as Given / When / Then. Pace should be calculated from distance and time, not typed in.

## Agent response (summary)

Drafted PLAN.md with 4 tables (users, routes, runs, stars), 11 numbered features (7 spine + 4 of mine), two Given/When/Then tests, Flask + PostgreSQL on Render, the weekly streak as the main risk and CSV export as the first cut. Pace is computed as duration / distance instead of stored.
