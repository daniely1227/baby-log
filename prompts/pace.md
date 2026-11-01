# Prompt log for pace (my feature 8)

## Prompt

> Build my feature 8 from PLAN.md on the branch feature/pace. Pace is minutes per km, calculated from the run's time and distance, never typed in or stored. Show it in bold on every run row and on the detail page (for example "5:30 /km"). Add "Fastest pace" to the sort options. On the dashboard add two cards, average pace over the last 30 days and best pace (with the run's distance and date), and a line chart of pace for the last 10 runs. For the average, use total time divided by total km, not the average of each run's pace, so a long run counts more than a short one.

## Agent response (summary)

Added Run.pace_sec_per_km and Run.pace_text, a format_pace() helper registered as a template filter, a "fastest" sort that orders by duration_sec / distance_km in the database, and average_pace(), best_pace_run() and pace_trend() in stats.py. The pace chart labels its y-axis in min:sec per km.

## Checked

Runs of 5 km in 30:00, 10 km in 55:00 and 4 km in 26:00 gave paces of 6:00, 5:30 and 6:30 /km; "Fastest pace" sorted them 5:30, 6:00, 6:30; best pace = 5:30 /km; the 30-day average was 5:51 /km (6660 s / 19 km), not 6:00 (the plain average of the three paces), which confirms long runs weigh more. With no runs, the pace cards show a dash.
