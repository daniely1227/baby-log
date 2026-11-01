# Prompt log for find things (feature 6)

## Prompt

> Build feature 6 from PLAN.md on the branch feature/find. On the Runs page add a filter bar: search box for notes, a route filter (all routes, each of my routes, or "no route"), a month filter, and sort options newest first, oldest first and longest distance. Keep the filters in the URL so I can bookmark them. Show how many runs and how many km match. When nothing matches, say "No runs match these filters" with a Clear button.

## Agent response (summary)

Extended /runs to read q, route, month and sort from the URL and build the query step by step (case-insensitive notes search, route filter that only accepts my own route ids, a month from the 1st to the 1st of the next month). Sort orders live in one SORTS table so a new sort can be added in one line. Added the filter form, a "3 runs · 23.0 km" summary line, and separate empty states.

## Checked

With runs of 8 km (Sept, Hills), 5 km (Oct 30, Marina) and 10 km (Oct 31, no route), the results were newest = 10, 5, 8; oldest = 8, 5, 10; longest = 10, 8, 5; route=Marina → 5; no route → 10; month=2026-09 → 8; "windy" → 10 and 5. A nonsense month shows a message instead of crashing, and a route id that isn't mine is ignored.
