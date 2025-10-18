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
