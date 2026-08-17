from __future__ import annotations

from datetime import datetime, timezone
import math

from flask import Blueprint, jsonify, request
from sqlalchemy import func, text

from .extensions import db
from .models import Arrow, End, Practice, Round, User


api = Blueprint("api", __name__, url_prefix="/api")
MAX_ARROWS_PER_END = 6
DEFAULT_DISTANCE_METERS = 50
DEFAULT_TARGET_FACE_CM = 80
DEFAULT_TARGET_FACE_TYPE = "compound"
VALID_TARGET_FACE_TYPES = ("compound", "recurve")
INNER_TEN_SCORE_RADIUS_CM = 2.339
VALID_ARROW_SCORE_MARKS = {"", "X", "M"}


class ValidationError(ValueError):
    pass


@api.errorhandler(ValidationError)
def handle_validation_error(error: ValidationError):
    db.session.rollback()
    return jsonify({"message": str(error)}), 400


def require_json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    return data


def clean_text(value: object, field_name: str, *, required: bool = False) -> str:
    if value is None:
        value = ""

    if not isinstance(value, str):
        value = str(value)

    cleaned = value.strip()
    if required and not cleaned:
        raise ValidationError(f"{field_name} is required.")

    return cleaned


def parse_int(value: object, field_name: str, *, minimum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be an integer.") from exc

    if minimum is not None and parsed < minimum:
        raise ValidationError(f"{field_name} must be at least {minimum}.")

    return parsed


def parse_float(value: object, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a number.") from exc


def clean_target_face_type(value: object) -> str:
    cleaned = clean_text(value, "target_face_type")
    if cleaned not in VALID_TARGET_FACE_TYPES:
        raise ValidationError(
            f"target_face_type must be one of {', '.join(VALID_TARGET_FACE_TYPES)}."
        )
    return cleaned


def clean_arrow_score_mark(value: object) -> str:
    cleaned = clean_text(value, "score_mark").upper()
    if cleaned not in VALID_ARROW_SCORE_MARKS:
        raise ValidationError("score_mark must be X, M, or empty.")
    return cleaned


def derive_arrow_score_mark(score: int, x: float, y: float) -> str:
    if score == 0:
        return "M"

    if score == 10 and math.hypot(x, y) <= INNER_TEN_SCORE_RADIUS_CM:
        return "X"

    return ""


def require_record(model, record_id: int, *, name: str):
    record = db.session.get(model, record_id)
    if record is None:
        return jsonify({"message": f"{name} not found."}), 404
    return record


def load_user(user_id: int):
    return require_record(User, user_id, name="User")


def load_practice(practice_id: int):
    return require_record(Practice, practice_id, name="Practice")


def load_round(round_id: int):
    return require_record(Round, round_id, name="Round")


def load_end(end_id: int):
    return require_record(End, end_id, name="End")


def load_arrow(arrow_id: int):
    return require_record(Arrow, arrow_id, name="Arrow")


def apply_user_payload(user: User, data: dict) -> User:
    user.name = clean_text(data.get("name"), "name", required=True)
    password = clean_text(data.get("password"), "password")

    if password:
        user.set_password(password)
    elif user.id is None:
        raise ValidationError("password is required.")

    return user


def find_users_by_name(username: str) -> list[User]:
    return (
        User.query.filter(func.lower(User.name) == username.lower())
        .order_by(User.created_at.desc(), User.id.desc())
        .all()
    )


def apply_practice_payload(practice: Practice, data: dict) -> Practice:
    user_id = parse_int(data.get("user_id"), "user_id", minimum=1)
    if db.session.get(User, user_id) is None:
        raise ValidationError("user_id does not reference an existing user.")

    practice.user_id = user_id
    if "distance_meters" in data or practice.id is None:
        practice.distance_meters = parse_int(
            data.get("distance_meters", practice.distance_meters or DEFAULT_DISTANCE_METERS),
            "distance_meters",
            minimum=1,
        )
    if "target_face_cm" in data or practice.id is None:
        practice.target_face_cm = parse_int(
            data.get("target_face_cm", practice.target_face_cm or DEFAULT_TARGET_FACE_CM),
            "target_face_cm",
            minimum=1,
        )
    if practice.id is None:
        raw_target_face_type = data.get("target_face_type")
        if raw_target_face_type is None:
            practice.target_face_type = DEFAULT_TARGET_FACE_TYPE
        else:
            practice.target_face_type = clean_target_face_type(raw_target_face_type)
    elif "target_face_type" in data and data.get("target_face_type") is not None:
        target_face_type = clean_target_face_type(data.get("target_face_type"))
        if target_face_type != practice.target_face_type:
            raise ValidationError("target_face_type cannot be changed after creation.")
    practice.notes = clean_text(data.get("notes"), "notes")
    return practice


def apply_round_payload(round_record: Round, data: dict) -> Round:
    practice_id = parse_int(data.get("practice_id"), "practice_id", minimum=1)
    if db.session.get(Practice, practice_id) is None:
        raise ValidationError("practice_id does not reference an existing practice.")

    round_record.practice_id = practice_id
    round_record.name = clean_text(data.get("name"), "name", required=True)
    round_record.notes = clean_text(data.get("notes"), "notes")
    return round_record


def apply_end_payload(end_record: End, data: dict) -> End:
    round_id = parse_int(data.get("round_id"), "round_id", minimum=1)
    if db.session.get(Round, round_id) is None:
        raise ValidationError("round_id does not reference an existing round.")

    end_record.round_id = round_id
    if "end_number" in data and data.get("end_number") is not None:
        end_record.end_number = parse_int(data.get("end_number"), "end_number", minimum=1)
    end_record.notes = clean_text(data.get("notes"), "notes")
    return end_record


def apply_arrow_payload(arrow: Arrow, data: dict) -> Arrow:
    end_id = parse_int(data.get("end_id"), "end_id", minimum=1)
    if db.session.get(End, end_id) is None:
        raise ValidationError("end_id does not reference an existing end.")

    arrow_number = parse_int(data.get("arrow_number"), "arrow_number", minimum=1)
    if arrow_number > MAX_ARROWS_PER_END:
        raise ValidationError(f"arrow_number must be {MAX_ARROWS_PER_END} or lower.")

    existing_arrow_count = db.session.query(func.count(Arrow.id)).filter(Arrow.end_id == end_id)
    if arrow.id is not None:
        existing_arrow_count = existing_arrow_count.filter(Arrow.id != arrow.id)

    if existing_arrow_count.scalar() >= MAX_ARROWS_PER_END:
        raise ValidationError(f"An end can contain at most {MAX_ARROWS_PER_END} arrows.")

    score = parse_int(data.get("score"), "score", minimum=0)
    if score > 10:
        raise ValidationError("score must be 10 or lower.")

    x = parse_float(data.get("x", 0), "x")
    y = parse_float(data.get("y", 0), "y")
    score_mark = clean_arrow_score_mark(data.get("score_mark"))
    if not score_mark:
        score_mark = derive_arrow_score_mark(score, x, y)
    elif score_mark == "X" and score != 10:
        raise ValidationError("score_mark X requires score 10.")
    elif score_mark == "M" and score != 0:
        raise ValidationError("score_mark M requires score 0.")

    arrow.end_id = end_id
    arrow.arrow_number = arrow_number
    arrow.score = score
    arrow.score_mark = score_mark
    arrow.x = x
    arrow.y = y
    arrow.notes = clean_text(data.get("notes"), "notes")
    return arrow


def next_round_order(practice_id: int, *, exclude_round_id: int | None = None) -> int:
    query = db.session.query(func.max(Round.round_order)).filter(Round.practice_id == practice_id)
    if exclude_round_id is not None:
        query = query.filter(Round.id != exclude_round_id)

    max_order = query.scalar()
    return int(max_order or 0) + 1


def next_end_number(round_id: int, *, exclude_end_id: int | None = None) -> int:
    query = db.session.query(func.max(End.end_number)).filter(End.round_id == round_id)
    if exclude_end_id is not None:
        query = query.filter(End.id != exclude_end_id)

    max_number = query.scalar()
    return int(max_number or 0) + 1


def resequence_rounds(practice_id: int) -> None:
    rounds = (
        Round.query.filter(Round.practice_id == practice_id)
        .order_by(Round.round_order.asc(), Round.created_at.asc(), Round.id.asc())
        .all()
    )

    for index, round_record in enumerate(rounds, start=1):
        round_record.round_order = index


def resequence_ends(round_id: int) -> None:
    ends = (
        End.query.filter(End.round_id == round_id)
        .order_by(End.end_number.asc(), End.created_at.asc(), End.id.asc())
        .all()
    )

    for index, end_record in enumerate(ends, start=1):
        end_record.end_number = index


@api.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db.session.rollback()
        return (
            jsonify(
                {
                    "status": "degraded",
                    "service": "backend",
                    "database": "unavailable",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            503,
        )

    return jsonify(
        {
            "status": "ok",
            "service": "backend",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@api.post("/auth/login")
def login():
    data = require_json_body()
    username = clean_text(data.get("username"), "username", required=True)
    password = clean_text(data.get("password"), "password", required=True)
    matching_users = find_users_by_name(username)

    for user in matching_users:
        if user.check_password(password):
            return jsonify({"created": False, "user": user.to_dict()})

    passwordless_user = next((user for user in matching_users if not user.password), None)
    if passwordless_user is not None:
        passwordless_user.set_password(password)
        db.session.commit()
        return jsonify(
            {
                "created": False,
                "password_initialized": True,
                "user": passwordless_user.to_dict(),
            }
        )

    if matching_users:
        return jsonify({"message": "Invalid username or password."}), 401

    user = User(name=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"created": True, "user": user.to_dict()}), 201


@api.route("/users", methods=["GET", "POST"])
def users_collection():
    if request.method == "GET":
        users = User.query.order_by(User.created_at.desc(), User.id.desc()).all()
        return jsonify([user.to_dict() for user in users])

    user = apply_user_payload(User(), require_json_body())
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@api.route("/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
def users_item(user_id: int):
    user = load_user(user_id)
    if not isinstance(user, User):
        return user

    if request.method == "GET":
        return jsonify(user.to_dict())

    if request.method == "PUT":
        apply_user_payload(user, require_json_body())
        db.session.commit()
        return jsonify(user.to_dict())

    db.session.delete(user)
    db.session.commit()
    return "", 204


@api.route("/practices", methods=["GET", "POST"])
def practices_collection():
    if request.method == "GET":
        query = Practice.query
        user_id = request.args.get("user_id")
        if user_id:
            query = query.filter(Practice.user_id == parse_int(user_id, "user_id", minimum=1))

        practices = query.order_by(Practice.created_at.desc(), Practice.id.desc()).all()
        return jsonify([practice.to_dict() for practice in practices])

    practice = apply_practice_payload(Practice(), require_json_body())
    db.session.add(practice)
    db.session.commit()
    return jsonify(practice.to_dict()), 201


@api.route("/practices/<int:practice_id>", methods=["GET", "PUT", "DELETE"])
def practices_item(practice_id: int):
    practice = load_practice(practice_id)
    if not isinstance(practice, Practice):
        return practice

    if request.method == "GET":
        return jsonify(practice.to_dict())

    if request.method == "PUT":
        apply_practice_payload(practice, require_json_body())
        db.session.commit()
        return jsonify(practice.to_dict())

    db.session.delete(practice)
    db.session.commit()
    return "", 204


@api.route("/rounds", methods=["GET", "POST"])
def rounds_collection():
    if request.method == "GET":
        query = Round.query
        practice_id = request.args.get("practice_id")
        if practice_id:
            query = query.filter(
                Round.practice_id == parse_int(practice_id, "practice_id", minimum=1)
            )

        rounds = query.order_by(Round.round_order.asc(), Round.id.asc()).all()
        return jsonify([round_record.to_dict() for round_record in rounds])

    round_record = apply_round_payload(Round(), require_json_body())
    round_record.round_order = next_round_order(round_record.practice_id)
    db.session.add(round_record)
    db.session.commit()
    return jsonify(round_record.to_dict()), 201


@api.route("/rounds/<int:round_id>", methods=["GET", "PUT", "DELETE"])
def rounds_item(round_id: int):
    round_record = load_round(round_id)
    if not isinstance(round_record, Round):
        return round_record

    if request.method == "GET":
        return jsonify(round_record.to_dict())

    if request.method == "PUT":
        previous_practice_id = round_record.practice_id
        apply_round_payload(round_record, require_json_body())
        if round_record.practice_id != previous_practice_id:
            round_record.round_order = next_round_order(
                round_record.practice_id,
                exclude_round_id=round_record.id,
            )
            resequence_rounds(previous_practice_id)

        resequence_rounds(round_record.practice_id)
        db.session.commit()
        return jsonify(round_record.to_dict())

    practice_id = round_record.practice_id
    db.session.delete(round_record)
    resequence_rounds(practice_id)
    db.session.commit()
    return "", 204


@api.route("/ends", methods=["GET", "POST"])
def ends_collection():
    if request.method == "GET":
        query = End.query
        round_id = request.args.get("round_id")
        if round_id:
            query = query.filter(End.round_id == parse_int(round_id, "round_id", minimum=1))

        ends = query.order_by(End.end_number.asc(), End.id.asc()).all()
        return jsonify([end_record.to_dict() for end_record in ends])

    end_record = apply_end_payload(End(), require_json_body())
    end_record.end_number = next_end_number(end_record.round_id)
    db.session.add(end_record)
    db.session.commit()
    return jsonify(end_record.to_dict()), 201


@api.route("/ends/<int:end_id>", methods=["GET", "PUT", "DELETE"])
def ends_item(end_id: int):
    end_record = load_end(end_id)
    if not isinstance(end_record, End):
        return end_record

    if request.method == "GET":
        return jsonify(end_record.to_dict())

    if request.method == "PUT":
        previous_round_id = end_record.round_id
        apply_end_payload(end_record, require_json_body())
        if end_record.round_id != previous_round_id:
            end_record.end_number = next_end_number(
                end_record.round_id,
                exclude_end_id=end_record.id,
            )
            resequence_ends(previous_round_id)

        resequence_ends(end_record.round_id)
        db.session.commit()
        return jsonify(end_record.to_dict())

    round_id = end_record.round_id
    db.session.delete(end_record)
    resequence_ends(round_id)
    db.session.commit()
    return "", 204


@api.route("/arrows", methods=["GET", "POST"])
def arrows_collection():
    if request.method == "GET":
        query = Arrow.query
        end_id = request.args.get("end_id")
        if end_id:
            query = query.filter(Arrow.end_id == parse_int(end_id, "end_id", minimum=1))

        arrows = query.order_by(Arrow.arrow_number.asc(), Arrow.id.asc()).all()
        return jsonify([arrow.to_dict() for arrow in arrows])

    arrow = apply_arrow_payload(Arrow(), require_json_body())
    db.session.add(arrow)
    db.session.commit()
    return jsonify(arrow.to_dict()), 201


@api.route("/arrows/<int:arrow_id>", methods=["GET", "PUT", "DELETE"])
def arrows_item(arrow_id: int):
    arrow = load_arrow(arrow_id)
    if not isinstance(arrow, Arrow):
        return arrow

    if request.method == "GET":
        return jsonify(arrow.to_dict())

    if request.method == "PUT":
        apply_arrow_payload(arrow, require_json_body())
        db.session.commit()
        return jsonify(arrow.to_dict())

    db.session.delete(arrow)
    db.session.commit()
    return "", 204
