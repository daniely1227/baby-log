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

    stars = db.relationship("Star", backref="run", lazy=True, cascade="all, delete-orphan")

    def is_starred_by(self, user):
        return any(s.user_id == user.id for s in self.stars)

    @property
    def duration_text(self):
        return format_duration(self.duration_sec)

    @property
    def pace_sec_per_km(self):
        """Seconds per km, calculated from time and distance (never stored)."""
        if not self.distance_km or not self.duration_sec:
            return None
        return self.duration_sec / self.distance_km

    @property
    def pace_text(self):
        return format_pace(self.pace_sec_per_km)


class Star(db.Model):
    """Junction table: one row means "this user starred this run"."""

    __tablename__ = "stars"
    __table_args__ = (db.UniqueConstraint("user_id", "run_id", name="uq_star_user_run"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    run_id = db.Column(db.Integer, db.ForeignKey("runs.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def format_duration(seconds):
    """3725 -> '1:02:05', 1935 -> '32:15'."""
    if seconds is None:
        return ""
    h, rest = divmod(int(seconds), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse_duration(text):
    """'32:15' or '1:02:05' -> seconds. Digits without colons work too, read from the right
    the same way the form fills them in ('3215' -> 32:15, '10530' -> 1:05:30), in case the
    page's script didn't run. Raises ValueError if the format is wrong."""
    text = (text or "").strip()
    if text.isdecimal() and 3 <= len(text) <= 6:
        text = f"{text[:-4]}:{text[-4:-2]}:{text[-2:]}" if len(text) > 4 else f"{text[:-2]}:{text[-2:]}"
    parts = text.split(":")
    if len(parts) not in (2, 3) or not all(p.isdecimal() for p in parts):
        raise ValueError("bad duration")
    nums = [int(p) for p in parts]
    if len(nums) == 2:
        h, m, s = 0, nums[0], nums[1]
    else:
        h, m, s = nums
    if m >= 60 and len(nums) == 3 or s >= 60:
        raise ValueError("bad duration")
    return h * 3600 + m * 60 + s


def format_date(value, pattern):
    """strftime that also works on Windows, which doesn't know %-d, %-m or %-I
    (day, month and 12-hour clock hour without a leading zero)."""
    if value is None:
        return ""
    pattern = (pattern.replace("%-d", str(value.day))
                      .replace("%-m", str(value.month))
                      .replace("%-I", str(value.hour % 12 or 12)))
    return value.strftime(pattern)


def format_km(km):
    """5.0 -> '5', 5.2 -> '5.2', 3.333 -> '3.33'. Only shows the decimals that were typed."""
    if km is None:
        return ""
    return f"{round(km, 2):g}"


def format_pace(sec_per_km):
    """361.5 -> '6:02 /km'."""
    if sec_per_km is None:
        return ""
    total = int(round(sec_per_km))
    return f"{total // 60}:{total % 60:02d} /km"
