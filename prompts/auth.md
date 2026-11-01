# Prompt log for sign up and login (feature 1)

## Prompt

> Build feature 1 from PLAN.md on the branch feature/auth. Use Flask with Flask-Login and Flask-SQLAlchemy. Add a users table (id, email, password_hash, created_at). A new visitor can sign up with email and password from inside the app, then log in and log out. Store only a hashed password. Every page except sign up and log in should require login. Use the clean monochrome style from the Design section. Add a render.yaml so Render can deploy the app with a free PostgreSQL database.

## Agent response (summary)

Created app.py (app factory, sign up, log in, log out, a login-protected home page), models.py with the User model, templates for base / signup / login / home, a monochrome style.css, requirements.txt and render.yaml (free web service + free Postgres). It also converts Render's `postgres://` database URL to `postgresql://`, which SQLAlchemy requires.

## Checked

Signed up a test user, saw the home page with the email, logged out, and confirmed a wrong password shows "Email or password is wrong."
