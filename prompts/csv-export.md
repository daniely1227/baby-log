# Prompt log for CSV export (my feature 11)

## Prompt

> Build my feature 11 from PLAN.md on the branch feature/csv-export. Add a "Download CSV" button on the Runs page that downloads all my runs, oldest first, with columns date, time, route, distance_km, duration, pace_per_km, effort, notes and starred. Name the file with today's date. It has to open cleanly in Excel, including notes that contain commas. Only my own runs.

## Agent response (summary)

Added /export.csv, which writes rows with Python's csv module (so commas inside notes are quoted correctly), adds a byte-order mark so Excel reads it as UTF-8, and sends it as run-log-YYYY-MM-DD.csv. Pace is included as min:sec per km. It only reads the logged-in user's runs.

## Checked

Two runs came out oldest first; the note "windy, legs heavy" stayed in one quoted cell; 10 km in 1:02:05 showed pace 6:12; the starred run showed "yes"; another account's export had only the header row.
