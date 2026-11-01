# Prompt log for the Windows date fix

## Prompt

> Double-check everything you built before I deploy it, as thoroughly as you can.

## Agent response (summary)

Dates on the pages were written with `%-d` and `%-I` (day and hour without a leading zero, like "Nov 1" and "7:30 AM"). Mac and Linux understand those codes, but Windows doesn't, so anyone who follows the README on a Windows laptop would get a server error on every page that lists a run. The chart labels in stats.py had the same problem.

The pace chart labels also had a rounding slip. 5.995 minutes per km showed as "5:60" instead of "6:00".

Fixes
- New `format_date()` in models.py, used in the templates as `|date(...)`. It fills in the day, month and hour itself, then formats the rest normally.
- Chart labels in stats.py are built from the month and day numbers directly.
- The pace label now rounds to whole seconds first, then splits into minutes and seconds.

## Checked

For every half hour of 2026, `format_date()` gives exactly the same text as the old code did on Linux for all four date formats the app uses. No `%-` code reaches strftime anymore. The pace label gives 5:00, 5:30, 5:59, 6:00 for 5, 5.5, 5.99 and 5.995. All tests pass.
