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

from models import Route, Run, User, db

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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
