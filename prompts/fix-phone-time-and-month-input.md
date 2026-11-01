# Prompt log for the phone keyboard and month box fixes

## Prompt

> 그리고 다시 한번 do another pass. I grant all access and give you full authority.

## Agent response (summary)

The second pass looked at how the forms behave on real phones and browsers, which the automated clicks can't see because they type values straight into the page.

- The time box asked phones for a number-only keypad. On an iPhone that keypad has the digits 0 to 9 and nothing else, so there was no way to type the colon in 32:15, and a run could not be logged from an iPhone at all.
- The Month filter uses the browser's month picker. Chrome has one, but Safari and Firefox on a computer don't, and they show an empty text box with no hint of the format.
- Picking December 9999 in the month picker crashed the Runs page with a server error.

Fixes
- The time box now opens the normal keyboard, where the colon is on the numbers layer, and autocorrect is off so it can't change what was typed.
- The month box shows 2026-10 as an example, 2026/10 is accepted too, and whatever was typed is shown back as 2026-10.
- A month that runs past the year 9999 gets the normal "doesn't look right" message instead of a crash.

## Checked

The time box no longer has a numeric keyboard setting. On PostgreSQL, ?month=2026/10 and ?month=2026-10 return the same runs, ?month=9999-12 shows the message with no server error, and the full click-through still passes.
