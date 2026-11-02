# Prompt log for showing distances the way they were typed

## Prompt

> ㅇㅋ 그렇게하자

(Going with the plan to also fix stranger-test struggle number 1, where distance felt like it needed two decimals, and leave the black and white design as it is.)

## Agent response (summary)

Typing 5 or 5.2 always worked, but the run page showed "5.20 km" and the lists showed "5.0 km", which made it look as if two decimals were required. A new `format_km()` shows only the decimals that matter, so 5 shows as 5, 5.2 as 5.2 and 5.25 as 5.25. It's used on every page that shows a distance and in the form when a route fills in its distance. The arrows on the distance box now step by 0.1 instead of 0.01.

## Checked

In a browser, a 5 km route showed "5 km" on Routes, filled the form with 5, and the saved run showed "5 km in 35:15". A 5.25 km run showed "5.25 km", the list total read "10.25 km", and the home button and dashboard cards showed the same style. All tests pass.
