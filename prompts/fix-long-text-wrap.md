# Prompt log for the long-text layout fix

## Prompt

> Double-check everything you built before I deploy it, as thoroughly as you can.

## Agent response (summary)

On a phone, a route name made of one very long word (the test used 120 R's, the most the form allows) didn't wrap. It ran out of its "Same as last time" button, covered the next button and made the whole page scroll sideways. The same would happen with a long word in a note on the run page.

Fix
- Route names, notes, page titles and messages now break inside a long word when it doesn't fit, and the one-tap buttons are allowed to shrink to their column.

## Checked

With the 120-letter route saved, the home, runs, run, delete, dashboard, routes, starred and new-run pages have no sideways scrolling at 320 and 390 pixels wide, and the long name wraps inside its button. Normal names like "Berkeley Marina loop" look the same as before. The full click-through on PostgreSQL passed again (79 checks, no server errors).
