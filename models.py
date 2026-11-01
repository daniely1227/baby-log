from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    routes = db.relationship("Route", backref="user", lazy=True, cascade="all, delete-orphan")
    runs = db.relationship("Run", backref="user", lazy=True, cascade="all, delete-orphan")


class Route(db.Model):
    __tablename__ = "routes"

    SURFACES = ("road", "trail", "track", "treadmill")

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    distance_km = db.Column(db.Float)
    surface = db.Column(db.String(20))

    runs = db.relationship("Run", backref="route", lazy=True)


class Run(db.Model):
    __tablename__ = "runs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id"))
    run_at = db.Column(db.DateTime, nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    duration_sec = db.Column(db.Integer, nullable=False)
    effort = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def duration_text(self):
        return format_duration(self.duration_sec)


def format_duration(seconds):
    """3725 -> '1:02:05', 1935 -> '32:15'."""
    if seconds is None:
        return ""
    h, rest = divmod(int(seconds), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse_duration(text):
    """'32:15' or '1:02:05' -> seconds. Raises ValueError if the format is wrong."""
    parts = (text or "").strip().split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        raise ValueError("bad duration")
    nums = [int(p) for p in parts]
    if len(nums) == 2:
        h, m, s = 0, nums[0], nums[1]
    else:
        h, m, s = nums
    if m >= 60 and len(nums) == 3 or s >= 60:
        raise ValueError("bad duration")
    return h * 3600 + m * 60 + s
