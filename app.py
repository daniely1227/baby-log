import csv
import io
import math
import os
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy.exc import IntegrityError, ProgrammingError
from werkzeug.security import check_password_hash, generate_password_hash

from models import Route, Run, Star, User, db, format_date, format_duration, format_km, format_pace, parse_duration
from stats import dashboard_stats, days_since_last_run, weekly_streak

APP_TZ = ZoneInfo(os.environ.get("APP_TZ", "America/Los_Angeles"))


def now_local():
    """Current wall-clock time in Pacific time, without tz info."""
    return datetime.now(APP_TZ).replace(tzinfo=None, second=0, microsecond=0)


def parse_km(value):
    """'5.2' -> 5.2, '' -> None. Raises ValueError for text, and for 'nan' or 'inf',
    which Python would otherwise read as numbers."""
    value = (value or "").strip()
    if not value:
        return None
    km = float(value)
    if not math.isfinite(km):
        raise ValueError("not a real number")
    return km


def get_own_route(route_id):
    route = Route.query.filter_by(id=route_id, user_id=current_user.id).first()
    if route is None:
        abort(404)
    return route


def get_own_run(run_id):
    """Return a run only if it belongs to the logged-in user, else 404."""
    run = Run.query.filter_by(id=run_id, user_id=current_user.id).first()
    if run is None:
        abort(404)
    return run


def user_routes():
    return Route.query.filter_by(user_id=current_user.id).order_by(Route.name).all()


MAX_EMAIL = 255       # same as users.email
MAX_ROUTE_NAME = 120  # same as routes.name
MAX_DURATION_SEC = 100 * 3600  # 100 hours, far beyond any real run


def parse_run_at(text):
    """'2026-10-31T07:30' -> datetime. Raises ValueError for anything else."""
    value = datetime.fromisoformat((text or "").strip())
    if value.tzinfo is not None:
        raise ValueError("time zone not expected")
    return value


def looks_like_email(email):
    name, at, domain = email.partition("@")
    return bool(name) and at == "@" and "." in domain.strip(".") and " " not in email


def validate_run_form(form):
    """Return a list of friendly error messages. Empty list means the form is OK."""
    errors = []
    if not form.get("run_at", "").strip():
        errors.append("Please enter the date and time of the run.")
    else:
        try:
            run_at = parse_run_at(form["run_at"])
        except ValueError:
            errors.append("The date doesn't look right. Please pick it again.")
        else:
            if run_at.date() > now_local().date():
                errors.append("That date is in the future. Please pick the day you ran.")

    km = form.get("distance_km", "").strip()
    if not km:
        errors.append("Please enter the distance in km.")
    else:
        try:
            value = parse_km(km)
        except ValueError:
            errors.append("Distance must be a number of km, like 5.2.")
        else:
            if value <= 0:
                errors.append("Distance must be more than 0 km.")
            elif value > 200:
                errors.append("That distance looks too long. Please check the km.")

    duration = form.get("duration", "").strip()
    if not duration:
        errors.append("Please enter how long the run took, like 32:15.")
    else:
        try:
            seconds = parse_duration(duration)
        except ValueError:
            errors.append("Time should look like 32:15 (minutes:seconds) or 1:05:30.")
        else:
            if seconds == 0:
                errors.append("Time must be more than 0:00.")
            elif seconds >= MAX_DURATION_SEC:
                errors.append("That time looks too long. Please check it.")

    route_id = form.get("route_id") or ""
    if route_id and not (route_id.isdecimal() and
                         Route.query.filter_by(id=int(route_id), user_id=current_user.id).first()):
        errors.append("Please pick one of your own routes.")

    effort = form.get("effort") or ""
    if effort and effort not in {"1", "2", "3", "4", "5"}:
        errors.append("Effort must be between 1 and 5.")
    return errors


def form_preview(form):
    """A run object (not saved) that holds what the user typed, so the form can be shown again."""
    run = Run()
    try:
        run.run_at = parse_run_at(form.get("run_at"))
    except ValueError:
        run.run_at = None
    try:
        run.distance_km = float(form.get("distance_km", "").strip())
    except ValueError:
        run.distance_km = None
    rid = form.get("route_id") or ""
    run.route_id = int(rid) if rid.isdecimal() else None
    eff = form.get("effort") or ""
    run.effort = int(eff) if eff.isdecimal() else None
    run.notes = form.get("notes", "")
    return run


def fill_run_from_form(run, form):
    """Copy form values onto a run. Raises ValueError if something can't be read."""
    run.run_at = parse_run_at(form.get("run_at"))
    run.distance_km = float(form.get("distance_km", "").strip())
    run.duration_sec = parse_duration(form.get("duration"))
    route_id = form.get("route_id") or None
    run.route_id = int(route_id) if route_id else None
    effort = form.get("effort") or None
    run.effort = int(effort) if effort else None
    run.notes = form.get("notes", "").strip() or None
    return run


SORTS = {
    "newest": lambda: (Run.run_at.desc(),),
    "oldest": lambda: (Run.run_at.asc(),),
    "longest": lambda: (Run.distance_km.desc(), Run.run_at.desc()),
    "fastest": lambda: ((Run.duration_sec / Run.distance_km).asc(), Run.run_at.desc()),
}
SORT_LABELS = {
    "newest": "Newest first",
    "oldest": "Oldest first",
    "longest": "Longest distance",
    "fastest": "Fastest pace",
}


def database_url():
    url = os.environ.get("DATABASE_URL", "sqlite:///runlog.db")
    # Render gives postgres:// or postgresql:// with no driver name. Name the driver we
    # install (psycopg2), because newer SQLAlchemy versions look for a different one.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = "postgresql+psycopg2://" + url[len(prefix):]
    return url


def create_tables(tries=3):
    """Create any missing tables. On a brand-new database two web workers can start at the
    same moment and both try to create the tables; the slower one gets an error, so it waits
    a second and checks again (by then the tables exist and nothing is created twice)."""
    for attempt in range(tries):
        try:
            db.create_all()
            return
        except (IntegrityError, ProgrammingError):
            if attempt == tries - 1:
                raise
            time.sleep(1)


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url()
    # Test each saved database connection before using it, so a database restart on
    # Render doesn't turn the next page into a server error.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    # Don't send the login cookie with form posts that come from other websites.
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    if config:
        app.config.update(config)

    db.init_app(app)
    app.jinja_env.filters["pace"] = format_pace
    app.jinja_env.filters["date"] = format_date
    app.jinja_env.filters["km"] = format_km

    login_manager = LoginManager(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in first."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        create_tables()

    # ---------- Accounts ----------

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not email or not password:
                flash("Please enter an email and a password.")
            elif len(email) > MAX_EMAIL or not looks_like_email(email):
                flash("That email doesn't look right. Please check it.")
            elif len(password) < 6:
                flash("Password needs at least 6 characters.")
            elif User.query.filter_by(email=email).first():
                flash("That email already has an account. Try logging in.")
            else:
                user = User(email=email, password_hash=generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return redirect(url_for("home"))
        return render_template("signup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for("home"))
            flash("Email or password is wrong.")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("login"))

    # ---------- Pages ----------

    @app.route("/")
    @login_required
    def home():
        recent = (
            Run.query.filter_by(user_id=current_user.id).order_by(Run.run_at.desc()).limit(5).all()
        )
        quick = []
        for route in user_routes():
            last = (
                Run.query.filter_by(user_id=current_user.id, route_id=route.id)
                .order_by(Run.run_at.desc())
                .first()
            )
            quick.append({"route": route, "last": last})
        all_runs = Run.query.filter_by(user_id=current_user.id).all()
        now = now_local()
        return render_template(
            "home.html",
            recent=recent,
            quick=quick,
            days_since=days_since_last_run(all_runs, now),
            streak=weekly_streak(all_runs, now),
        )

    @app.route("/routes/<int:route_id>/repeat", methods=["POST"])
    @login_required
    def route_repeat(route_id):
        """One tap: log a run now on this route with the same distance and time as last time."""
        route = get_own_route(route_id)
        last = (
            Run.query.filter_by(user_id=current_user.id, route_id=route.id)
            .order_by(Run.run_at.desc())
            .first()
        )
        if last is None:
            flash(f"No earlier run on {route.name} to copy yet. Log this one with the form.")
            return redirect(url_for("run_new", route=route.id))
        run = Run(
            user_id=current_user.id,
            route_id=route.id,
            run_at=now_local(),
            distance_km=last.distance_km,
            duration_sec=last.duration_sec,
            effort=last.effort,
        )
        db.session.add(run)
        db.session.commit()
        flash(f"Logged {run.distance_km:g} km on {route.name} in {run.duration_text}. "
              "Tap Edit if today was different.")
        return redirect(url_for("run_detail", run_id=run.id))

    # ---------- Routes (places I run) ----------

    @app.route("/routes", methods=["GET", "POST"])
    @login_required
    def routes_page():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            surface = request.form.get("surface") or None
            try:
                km = parse_km(request.form.get("distance_km"))
            except ValueError:
                km = None
                flash("Distance must be a number of km, like 5.2.")
            else:
                if not name:
                    flash("Please give the route a name.")
                elif len(name) > MAX_ROUTE_NAME:
                    flash(f"Please keep the route name to {MAX_ROUTE_NAME} characters or fewer.")
                elif km is not None and km <= 0:
                    flash("Distance must be more than 0 km.")
                else:
                    db.session.add(Route(user_id=current_user.id, name=name, distance_km=km,
                                         surface=surface if surface in Route.SURFACES else None))
                    db.session.commit()
                    flash(f"Route \"{name}\" saved.")
                    return redirect(url_for("routes_page"))
        routes = Route.query.filter_by(user_id=current_user.id).order_by(Route.name).all()
        return render_template("routes.html", routes=routes)

    @app.route("/routes/<int:route_id>/delete", methods=["POST"])
    @login_required
    def route_delete(route_id):
        route = get_own_route(route_id)
        for run in route.runs:
            run.route_id = None
        db.session.delete(route)
        db.session.commit()
        flash("Route removed. Its runs were kept.")
        return redirect(url_for("routes_page"))

    # ---------- Runs: create / read / update / delete ----------

    @app.route("/runs")
    @login_required
    def runs_list():
        query = Run.query.filter_by(user_id=current_user.id)
        routes = user_routes()

        route_id = request.args.get("route", "")
        if route_id == "none":
            query = query.filter(Run.route_id.is_(None))
        elif route_id.isdecimal() and any(r.id == int(route_id) for r in routes):
            query = query.filter(Run.route_id == int(route_id))
        else:
            route_id = ""

        month = request.args.get("month", "")
        if month:
            try:
                # Chrome sends 2026-10 from its month picker. Safari and Firefox on a computer
                # show a plain text box instead, so also accept 2026/10.
                start = datetime.strptime(month.replace("/", "-"), "%Y-%m")
                end = (start + timedelta(days=32)).replace(day=1)
            except (ValueError, OverflowError):
                flash("That month doesn't look right, so it was ignored. Use a format like 2026-10.")
                month = ""
            else:
                month = start.strftime("%Y-%m")
                query = query.filter(Run.run_at >= start, Run.run_at < end)

        q = request.args.get("q", "").strip()
        if q:
            query = query.filter(Run.notes.ilike(f"%{q}%"))

        sort = request.args.get("sort", "newest")
        order = SORTS.get(sort)
        if order is None:
            sort, order = "newest", SORTS["newest"]
        runs = query.order_by(*order()).all()

        filters = {"route": route_id, "month": month, "q": q, "sort": sort}
        filtering = bool(route_id or month or q)
        return render_template("runs_list.html", runs=runs, routes=routes, filters=filters,
                               filtering=filtering, sort_labels=SORT_LABELS)

    @app.route("/runs/new", methods=["GET", "POST"])
    @login_required
    def run_new():
        run = Run(user_id=current_user.id, run_at=now_local())
        pre = request.args.get("route", "")
        if pre.isdecimal():
            route = Route.query.filter_by(id=int(pre), user_id=current_user.id).first()
            if route:
                run.route_id, run.distance_km = route.id, route.distance_km
        if request.method == "POST":
            errors = validate_run_form(request.form)
            if errors:
                return render_template("run_form.html", run=form_preview(request.form), is_new=True,
                                       routes=user_routes(), duration=request.form.get("duration", ""),
                                       errors=errors), 400
            fill_run_from_form(run, request.form)
            db.session.add(run)
            db.session.commit()
            flash("Run saved.")
            return redirect(url_for("run_detail", run_id=run.id))
        return render_template("run_form.html", run=run, is_new=True, routes=user_routes(), duration="")

    @app.route("/runs/<int:run_id>")
    @login_required
    def run_detail(run_id):
        return render_template("run_detail.html", run=get_own_run(run_id))

    @app.route("/runs/<int:run_id>/edit", methods=["GET", "POST"])
    @login_required
    def run_edit(run_id):
        run = get_own_run(run_id)
        if request.method == "POST":
            errors = validate_run_form(request.form)
            if errors:
                preview = form_preview(request.form)
                preview.id = run.id
                return render_template("run_form.html", run=preview, is_new=False, routes=user_routes(),
                                       duration=request.form.get("duration", ""), errors=errors), 400
            fill_run_from_form(run, request.form)
            db.session.commit()
            flash("Run updated.")
            return redirect(url_for("run_detail", run_id=run.id))
        return render_template("run_form.html", run=run, is_new=False, routes=user_routes(),
                               duration=run.duration_text)

    @app.route("/runs/<int:run_id>/delete", methods=["GET", "POST"])
    @login_required
    def run_delete(run_id):
        run = get_own_run(run_id)
        if request.method == "POST":
            db.session.delete(run)
            db.session.commit()
            flash("Run deleted.")
            return redirect(url_for("runs_list"))
        return render_template("run_delete.html", run=run)

    # ---------- CSV export ----------

    @app.route("/export.csv")
    @login_required
    def export_csv():
        runs = Run.query.filter_by(user_id=current_user.id).order_by(Run.run_at.asc()).all()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["date", "time", "route", "distance_km", "duration", "pace_per_km",
                         "effort", "notes", "starred"])
        for r in runs:
            writer.writerow([
                r.run_at.strftime("%Y-%m-%d"),
                r.run_at.strftime("%H:%M"),
                r.route.name if r.route else "",
                f"{r.distance_km:g}",
                r.duration_text,
                r.pace_text.replace(" /km", ""),
                r.effort or "",
                r.notes or "",
                "yes" if r.is_starred_by(current_user) else "",
            ])
        filename = f"run-log-{now_local().strftime('%Y-%m-%d')}.csv"
        return Response(
            "\ufeff" + buf.getvalue(),  # BOM so Excel opens it as UTF-8
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # ---------- Dashboard ----------

    @app.route("/dashboard")
    @login_required
    def dashboard():
        runs = Run.query.filter_by(user_id=current_user.id).all()
        return render_template("dashboard.html", stats=dashboard_stats(runs, now_local()))

    # ---------- Stars ----------

    @app.route("/runs/<int:run_id>/star", methods=["POST"])
    @login_required
    def run_star(run_id):
        run = get_own_run(run_id)
        star = Star.query.filter_by(user_id=current_user.id, run_id=run.id).first()
        if star:
            db.session.delete(star)
        else:
            db.session.add(Star(user_id=current_user.id, run_id=run.id))
        db.session.commit()
        nxt = request.form.get("next", "")
        # Only follow links inside this app. Browsers read "//site.com" and "/\site.com"
        # as another website, so both are refused.
        if not nxt.startswith("/") or nxt.startswith("//") or "\\" in nxt:
            nxt = url_for("run_detail", run_id=run.id)
        return redirect(nxt)

    @app.route("/starred")
    @login_required
    def starred():
        runs = (
            Run.query.join(Star, Star.run_id == Run.id)
            .filter(Star.user_id == current_user.id)
            .order_by(Run.run_at.desc())
            .all()
        )
        return render_template("starred.html", runs=runs)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
