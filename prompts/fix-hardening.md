# Prompt log for the database restart and odd-input fixes

## Prompt

> 그리고 다시 한번 do another pass. I grant all access and give you full authority.

## Agent response (summary)

The second pass restarted PostgreSQL while the app was running and sent the app inputs a normal form wouldn't, to see what breaks.

- After a database restart, the next page load was a server error ("server closed the connection unexpectedly"), because the app reused a connection the database had already closed. Render restarts databases for maintenance, so this could have hit during the demo.
- "nan" and "inf" were accepted as a distance, because Python reads them as numbers. A run saved with nan km would crash every page that shows it.
- A time like 999999999999:00 passed the format check and was too big for the database column.
- A superscript ² in a route or effort field counts as a digit in Python but can't be turned into a number, so it caused a server error.
- The star button's "go back to" link refused //other-site.com but not /\other-site.com, which browsers treat the same way.
- The login cookie had no SameSite setting, so it relied on each browser's default to stay off form posts from other websites.

Fixes
- Each saved database connection is tested before use (`pool_pre_ping`).
- Distances must be real numbers, times must be under 100 hours, and only plain digits count as numbers in ids and effort.
- The "go back to" link also refuses backslashes.
- The login cookie is set to SameSite=Lax.

## Checked

On PostgreSQL, the three page loads after a database restart all returned normally (before the fix the first one was a server error). nan, inf and -inf are refused for runs and routes with the usual message, 100:00:00 and 999999999999:00 are refused as too long while 99:59:59 is accepted, ² inputs get messages or are ignored, /\evil.com sends you back to the run, and the cookie now carries SameSite=Lax. No server errors in the log, all tests pass, and the full click-through passes.
