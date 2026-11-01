# Prompt log: data model and routes (feature 2)

## Prompt

> Build feature 2 from PLAN.md on the branch feature/data-model. Add the routes and runs tables exactly as in section 3 of the plan: routes belong to a user; runs belong to a user and optionally to a route. Store duration as seconds and add helpers that turn "32:15" or "1:02:05" into seconds and back. Add a Routes page where I can see my routes (with how many runs each has), add a route with a name, optional usual distance in km and surface, and remove a route without losing its runs. Times are Pacific time, not UTC.

## Agent response (summary)

Added Route and Run models (users → routes → runs, users → runs), parse_duration() and format_duration(), a now_local() helper in Pacific time, and a /routes page with an add form and a remove button. Removing a route unlinks its runs instead of deleting them, and a route can only be removed by its owner.

## Checked

Empty name and "abc" as km show messages; "Berkeley Marina loop, 5.2 km, road" saves and shows "5.2 km"; another account gets 404 trying to remove it. parse_duration("32:15") = 1935 and parse_duration("1:02:05") = 3725; "32", "a:b", "1:61:00" and "10:75" are rejected.
