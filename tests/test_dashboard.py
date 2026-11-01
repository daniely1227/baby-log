"""Test 2, dashboard stat.

Given a user logged runs of 5 km, 3.5 km and 10 km in the last 7 days
and a 20 km run 10 days ago,
when they open the dashboard,
then "km in the last 7 days" shows 18.5 km.
"""
import re
from datetime import timedelta

from app import now_local
from conftest import sign_up


def test_km_in_last_7_days_on_dashboard(app):
    client = app.test_client()
    sign_up(client, "runner@example.com")

    now = now_local()
    runs = [(1, "5"), (3, "3.5"), (6, "10"), (10, "20")]  # (days ago, km)
    for days_ago, km in runs:
        when = (now - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M")
        client.post("/runs/new", data={"run_at": when, "distance_km": km, "duration": "30:00"})

    page = client.get("/dashboard").data.decode()
    shown = re.search(r'id="stat-km-7d">([^<]+)<', page).group(1)
    assert shown == "18.5 km"
