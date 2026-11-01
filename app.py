import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

from models import Route, Run, Star, User, db, format_duration, parse_duration
from stats import dashboard_stats

APP_TZ = ZoneInfo(os.environ.get("APP_TZ", "America/Los_Angeles"))


def now_local():
    """Current wall-clock time in Pacific time, without tz info."""
    return datetime.now(APP_TZ).replace(tzinfo=None, second=0, microsecond=0)


def parse_km(value):
    value = (value or "").strip()
    return float(value) if value else None


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


def validate_run_form(form):
    """Return a list of friendly error messages. Empty list means the form is OK."""
    errors = []
    try:
        if not form.get("run_at", "").strip():
            errors.append("Please enter the date and time of the run.")
        else:
            datetime.fromisoformat(form["run_at"].strip())
    except ValueError:
        errors.append("The date doesn't look right. Please pick it again.")

    km = form.get("distance_km", "").strip()
    if not km:
        errors.append("Please enter the distance in km.")
    else:
        try:
            value = float(km)
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
            if parse_duration(duration) == 0:
                errors.append("Time must be more than 0:00.")
        except ValueError:
            errors.append("Time should look like 32:15 (minutes:seconds) or 1:05:30.")

    route_id = form.get("route_id") or ""
    if route_id and not (route_id.isdigit() and
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
        run.run_at = datetime.fromisoformat(form.get("run_at", "").strip())
    except ValueError:
        run.run_at = None
    try:
        run.distance_km = float(form.get("distance_km", "").strip())
    except ValueError:
        run.distance_km = None
    rid = form.get("route_id") or ""
    run.route_id = int(rid) if rid.isdigit() else None
    eff = form.get("effort") or ""
    run.effort = int(eff) if eff.isdigit() else None
    run.notes = form.get("notes", "")
    return run


def fill_run_from_form(run, form):
    """Copy form values onto a run. Raises ValueError if something can't be read."""
    run.run_at = datetime.fromisoformat(form.get("run_at", "").strip())
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
}
SORT_LABELS = {"newest": "Newest first", "oldest": "Oldest first", "longest": "Longest distance"}


def database_url():
    url = os.environ.get("DATABASE_URL", "sqlite:///runlog.db")
    # Render gives postgres:// but SQLAlchemy wants postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url()
    if config:
        app.config.update(config)

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in first."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

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
        return render_template("home.html")

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
        elif route_id.isdigit() and any(r.id == int(route_id) for r in routes):
            query = query.filter(Run.route_id == int(route_id))
        else:
            route_id = ""

        month = request.args.get("month", "")
        if month:
            try:
                start = datetime.strptime(month, "%Y-%m")
            except ValueError:
                flash("That month doesn't look right, so it was ignored.")
                month = ""
            else:
                end = (start + timedelta(days=32)).replace(day=1)
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
        # Only follow links inside this app (no "//other-site.com" redirects).
        if not nxt.startswith("/") or nxt.startswith("//"):
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
