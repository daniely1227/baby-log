# Prompt log for test 1, data isolation

## Prompt

> On the branch test/data-isolation, write a pytest test for test 1 in PLAN.md section 4. Given User A has logged one run, when User B signs up, opens the runs list and tries to open User A's run by its URL, then User B sees an empty list and gets "not found" for User A's run. Also check B can't edit, delete or star A's run by URL. Use a fresh in-memory database for every test.
>
> Then prove the test works: temporarily remove the user check from get_own_run(), run the test and capture it failing, put the check back, and capture it passing.

## Agent response (summary)

Added tests/conftest.py (an app fixture with an in-memory SQLite database and a sign_up helper) and tests/test_data_isolation.py. With the user check removed, User B could open /runs/1 and the test failed with "assert 200 == 404". With the check restored, it passed.

## Screenshots

- docs/screenshots/isolation-red.png
- docs/screenshots/isolation-green.png
