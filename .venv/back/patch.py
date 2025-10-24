from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from .db import conn, cur

patch_bp = Blueprint('patch_bp', __name__)

@patch_bp.route('/user', methods=['PATCH'])
# @role_required(['admin', 'moderator'])
def patch_user():
    try:
        if not request.is_json:
            return jsonify(error="NOT JSON"), 400

        data = request.get_json()
        inn = data.get("inn")
        if not inn:
            return jsonify(error="Missing inn"), 400

        updatable_fields = ["last_name", "middle_name", "first_name",
                            "department_id", "role", "company_ogrn", "schedule_id"]

        sets = []
        params = []

        for field in updatable_fields:
            if field in data and data[field] is not None:
                sets.append(f"{field} = %s")
                params.append(data[field])

        if not sets:
            return jsonify(message="No fields to update"), 400

        params.append(inn)
        sql = f"UPDATE public.users SET {', '.join(sets)} WHERE inn = %s;"

        cur.execute(sql, tuple(params))
        conn.commit()

        return jsonify(message="User updated"), 200

    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400

@patch_bp.route('/sch', methods=['PATCH'])
# @role_required(['admin', 'moderator'])
def patch_schedule():
    try:
        if not request.is_json:
            return jsonify(error="NOT JSON"), 400

        data = request.get_json()
        schedule_id = data.get("id")
        if not schedule_id:
            return jsonify(error="Missing schedule id"), 400

        updatable_fields = ["start", "stop", "pause", "free"]

        sets = []
        params = []

        for field in updatable_fields:
            if field in data and data[field] is not None:
                sets.append(f"{field} = %s")
                params.append(data[field])

        if not sets:
            return jsonify(message="No fields to update"), 400

        params.append(schedule_id)
        sql = f"UPDATE public.schedule SET {', '.join(sets)} WHERE id = %s;"

        cur.execute(sql, tuple(params))
        conn.commit()

        return jsonify(message="Schedule updated"), 200

    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400


@patch_bp.route('/jour/note', methods=['PATCH'])
# @role_required(['admin', 'moderator'])
def patch_journal_note():
    try:
        if not request.is_json:
            return jsonify(error="NOT JSON"), 400

        data = request.get_json()
        journal_id = data.get("id")
        note = data.get("note")

        if not all([journal_id]):
            return jsonify(error="Missing required identifiers"), 400

        if note is None:
            return jsonify(error="Nothing to update"), 400

        sql = """
            UPDATE public.journal
            SET note = %s
            WHERE id = %s;
        """

        cur.execute(sql, (note, journal_id))
        conn.commit()

        return jsonify(message="Journal note updated"), 200

    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400

