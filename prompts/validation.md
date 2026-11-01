# Prompt log: validation (feature 4)

## Prompt

> Build feature 4 from PLAN.md on the branch feature/validation. Replace the generic "Please check the form." with specific friendly messages. Required: date and time, distance above 0 km, and a time like 32:15 or 1:05:30. Also catch a distance that isn't a number, an unrealistic distance, a route that isn't mine, and an effort outside 1 to 5. Don't save anything when there is a problem; show all messages at the top of the form and keep what I already typed.

## Agent response (summary)

Added validate_run_form(), which returns a list of plain-English messages, and form_preview(), which rebuilds an unsaved run from what was typed so the form can be shown again with the same values. Both the add and edit routes use them. A failed edit never changes the stored run.

## Bug caught

In feature 3, a form posted with someone else's route id would have linked my run to their route, because the route was never checked. Validation now only accepts my own routes.

## Checked

Blank date, blank distance, 0 km, "30" as time, blank time and route id 99 each show their own message with status 400; "abc" km keeps my notes and "30:00" in the form; a valid run saves; editing a saved run to -1 km is rejected and the stored 5.0 km is unchanged.
