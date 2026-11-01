# Prompt log for the long-input and future-date fixes

## Prompt

> Double-check everything you built before I deploy it, as thoroughly as you can.

## Agent response (summary)

The click-through on PostgreSQL found three things the SQLite tests missed.

- A route name longer than 120 characters or an email longer than 255 characters crashed the page with a server error. SQLite ignores column lengths, but PostgreSQL enforces them.
- A run dated in the future was saved, and the home page then said "Last run -3 days ago".
- Sign up accepted "notanemail" as an email.

Fixes
- Route names over 120 characters and emails over 255 characters now get a friendly message, and the two inputs stop typing at those lengths.
- Sign up checks that the email has a name, an @ and a domain with a dot.
- A run date after today shows "That date is in the future. Please pick the day you ran." A run later today is still fine.
- A date sent with a time zone on the end is treated as a bad date instead of being saved.

## Checked

On PostgreSQL, a 200-character route name and a 262-character email now show messages instead of a server error, a 120-character route name still saves, "notanemail" is refused while "A.B+c@mail.berkeley.edu" is accepted, tomorrow's date is refused, 11:59 PM today is accepted, and there were no server errors in the log.
