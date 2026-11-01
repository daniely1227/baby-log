"""Test 1, data isolation.

Given User A has logged one run,
when User B signs up, opens the runs list and tries to open User A's run by its URL,
then User B sees an empty list and gets a "not found" page for User A's run.
"""
from conftest import sign_up


def test_user_b_cannot_see_user_a_runs(app):
    user_a = app.test_client()
    user_b = app.test_client()

    # User A signs up and logs one run.
    sign_up(user_a, "a@example.com")
    resp = user_a.post(
        "/runs/new",
        data={"run_at": "2026-10-31T07:30", "distance_km": "5.2", "duration": "31:12",
              "notes": "User A secret note"},
    )
    a_run_url = resp.headers["Location"]  # e.g. /runs/1
    assert b"User A secret note" in user_a.get(a_run_url).data

    # User B signs up separately.
    sign_up(user_b, "b@example.com")

    # B's list is empty and does not contain A's run.
    b_list = user_b.get("/runs").data
    assert b"No runs yet" in b_list
    assert b"User A secret note" not in b_list

    # B cannot open, edit, delete or star A's run by guessing the URL.
    assert user_b.get(a_run_url).status_code == 404
    assert user_b.get(a_run_url + "/edit").status_code == 404
    assert user_b.post(a_run_url + "/delete").status_code == 404
    assert user_b.post(a_run_url + "/star").status_code == 404

    # A's run is still there after B's attempts.
    assert user_a.get(a_run_url).status_code == 200
