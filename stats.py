"""Dashboard numbers, computed from a list of runs.

Kept separate from the web routes so they are easy to test.
"""
from datetime import timedelta


def week_start(d):
    """Monday of the week that contains date d."""
    return d - timedelta(days=d.weekday())


def km_in_last_days(runs, now, days):
    since = now - timedelta(days=days)
    return round(sum(r.distance_km for r in runs if since <= r.run_at <= now), 2)


def runs_in_last_days(runs, now, days):
    since = now - timedelta(days=days)
    return sum(1 for r in runs if since <= r.run_at <= now)


def longest_run(runs):
    return max(runs, key=lambda r: r.distance_km, default=None)


def weekly_km(runs, now, weeks=8):
    """Return (labels, km) for the last `weeks` Monday-to-Sunday weeks, oldest first."""
    this_week = week_start(now.date())
    labels, totals = [], []
    for i in range(weeks - 1, -1, -1):
        start = this_week - timedelta(weeks=i)
        end = start + timedelta(days=7)
        labels.append(f"{start.month}/{start.day}")
        totals.append(round(sum(r.distance_km for r in runs if start <= r.run_at.date() < end), 1))
    return labels, totals


def average_pace(runs, now, days=30):
    """Average pace over the last `days` days: total time / total km (seconds per km)."""
    since = now - timedelta(days=days)
    recent = [r for r in runs if since <= r.run_at <= now and r.distance_km]
    km = sum(r.distance_km for r in recent)
    if not km:
        return None
    return sum(r.duration_sec for r in recent) / km


def best_pace_run(runs):
    """The run with the fastest pace (lowest seconds per km)."""
    paced = [r for r in runs if r.pace_sec_per_km]
    return min(paced, key=lambda r: r.pace_sec_per_km, default=None)


def pace_trend(runs, last=10):
    """(labels, minutes per km) for the last `last` runs, oldest first."""
    recent = sorted((r for r in runs if r.pace_sec_per_km), key=lambda r: r.run_at)[-last:]
    labels = [f"{r.run_at.month}/{r.run_at.day}" for r in recent]
    minutes = [round(r.pace_sec_per_km / 60, 2) for r in recent]
    return labels, minutes


def dashboard_stats(runs, now):
    labels, totals = weekly_km(runs, now)
    pace_labels, pace_minutes = pace_trend(runs)
    return {
        "avg_pace": average_pace(runs, now),
        "best_pace_run": best_pace_run(runs),
        "pace_labels": pace_labels,
        "pace_minutes": pace_minutes,
        "km_7d": km_in_last_days(runs, now, 7),
        "runs_30d": runs_in_last_days(runs, now, 30),
        "longest": longest_run(runs),
        "week_labels": labels,
        "week_km": totals,
        "total_runs": len(runs),
    }


def days_since_last_run(runs, now):
    """Whole days between the last run's date and today, or None if there are no runs."""
    if not runs:
        return None
    last = max(r.run_at for r in runs)
    return (now.date() - last.date()).days


def weekly_streak(runs, now):
    """How many Monday-to-Sunday weeks in a row have at least one run.

    The current week counts if it already has a run. If it doesn't yet, the streak
    is still alive and is counted from last week, because the week isn't over.
    """
    weeks_with_runs = {week_start(r.run_at.date()) for r in runs}
    week = week_start(now.date())
    if week not in weeks_with_runs:
        week -= timedelta(weeks=1)
    streak = 0
    while week in weeks_with_runs:
        streak += 1
        week -= timedelta(weeks=1)
    return streak
