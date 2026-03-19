from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(255), nullable=False, default="")

    practices = db.relationship(
        "Practice",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by=lambda: (Practice.created_at.desc(), Practice.id.desc()),
    )

    def set_password(self, password: str) -> None:
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password:
            return False
        return check_password_hash(self.password, password)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }


class Practice(TimestampMixin, db.Model):
    __tablename__ = "practices"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    distance_meters = db.Column(db.Integer, nullable=False, default=50)
    target_face_cm = db.Column(db.Integer, nullable=False, default=80)
    notes = db.Column(db.Text, nullable=False, default="")

    user = db.relationship("User", back_populates="practices")
    rounds = db.relationship(
        "Round",
        back_populates="practice",
        cascade="all, delete-orphan",
        order_by=lambda: (Round.round_order.asc(), Round.id.asc()),
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "distance_meters": self.distance_meters,
            "target_face_cm": self.target_face_cm,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class Round(TimestampMixin, db.Model):
    __tablename__ = "rounds"

    id = db.Column(db.Integer, primary_key=True)
    practice_id = db.Column(
        db.Integer,
        db.ForeignKey("practices.id"),
        nullable=False,
        index=True,
    )
    round_order = db.Column(db.Integer, nullable=False, default=1)
    name = db.Column(db.String(160), nullable=False)
    notes = db.Column(db.Text, nullable=False, default="")

    practice = db.relationship("Practice", back_populates="rounds")
    ends = db.relationship(
        "End",
        back_populates="round",
        cascade="all, delete-orphan",
        order_by=lambda: (End.end_number.asc(), End.id.asc()),
    )

    @property
    def total_score(self) -> int:
        if self.id is None:
            return 0

        total = (
            db.session.query(func.coalesce(func.sum(Arrow.score), 0))
            .join(End, Arrow.end_id == End.id)
            .filter(End.round_id == self.id)
            .scalar()
        )
        return int(total or 0)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "practice_id": self.practice_id,
            "round_order": self.round_order,
            "name": self.name,
            "notes": self.notes,
            "total_score": self.total_score,
            "created_at": self.created_at.isoformat(),
        }


class End(TimestampMixin, db.Model):
    __tablename__ = "ends"

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey("rounds.id"), nullable=False, index=True)
    end_number = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=False, default="")

    round = db.relationship("Round", back_populates="ends")
    arrows = db.relationship(
        "Arrow",
        back_populates="end",
        cascade="all, delete-orphan",
        order_by=lambda: (Arrow.arrow_number.asc(), Arrow.id.asc()),
    )

    @property
    def total_score(self) -> int:
        if self.id is None:
            return 0

        total = (
            db.session.query(func.coalesce(func.sum(Arrow.score), 0))
            .filter(Arrow.end_id == self.id)
            .scalar()
        )
        return int(total or 0)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "round_id": self.round_id,
            "end_number": self.end_number,
            "notes": self.notes,
            "total_score": self.total_score,
            "created_at": self.created_at.isoformat(),
        }


class Arrow(TimestampMixin, db.Model):
    __tablename__ = "arrows"

    id = db.Column(db.Integer, primary_key=True)
    end_id = db.Column(db.Integer, db.ForeignKey("ends.id"), nullable=False, index=True)
    arrow_number = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)
    score_mark = db.Column(db.String(1), nullable=False, default="")
    x = db.Column(db.Float, nullable=False, default=0.0)
    y = db.Column(db.Float, nullable=False, default=0.0)
    notes = db.Column(db.Text, nullable=False, default="")

    end = db.relationship("End", back_populates="arrows")

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "end_id": self.end_id,
            "arrow_number": self.arrow_number,
            "score": self.score,
            "score_mark": self.score_mark,
            "x": self.x,
            "y": self.y,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }
