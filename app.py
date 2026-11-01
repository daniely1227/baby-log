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

from models import Route, Run, User, db, format_duration, parse_duration

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
        runs = Run.query.filter_by(user_id=current_user.id).order_by(Run.run_at.desc()).all()
        return render_template("runs_list.html", runs=runs)

    @app.route("/runs/new", methods=["GET", "POST"])
    @login_required
    def run_new():
        run = Run(user_id=current_user.id, run_at=now_local())
        if request.method == "POST":
            try:
                fill_run_from_form(run, request.form)
            except ValueError:
                flash("Please check the form.")
                return render_template("run_form.html", run=run, is_new=True, routes=user_routes(),
                                       duration=request.form.get("duration", "")), 400
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
            try:
                fill_run_from_form(run, request.form)
            except ValueError:
                db.session.rollback()
                flash("Please check the form.")
                return render_template("run_form.html", run=run, is_new=False, routes=user_routes(),
                                       duration=request.form.get("duration", "")), 400
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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
