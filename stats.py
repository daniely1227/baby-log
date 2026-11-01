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
        labels.append(start.strftime("%-m/%-d"))
        totals.append(round(sum(r.distance_km for r in runs if start <= r.run_at.date() < end), 1))
    return labels, totals


def dashboard_stats(runs, now):
    labels, totals = weekly_km(runs, now)
    return {
        "km_7d": km_in_last_days(runs, now, 7),
        "runs_30d": runs_in_last_days(runs, now, 30),
        "longest": longest_run(runs),
        "week_labels": labels,
        "week_km": totals,
        "total_runs": len(runs),
    }
