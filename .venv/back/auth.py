from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from .db import conn, cur

auth_bp = Blueprint('auth', __name__)

def role_required(allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in allowed_roles:
                return jsonify({"Error": f"Доступ запрещён: недостаточно прав {user_role}"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@auth_bp.route('/reg', methods=['POST'])
def reg():
    try:
        if request.is_json:
            data = request.get_json()
            inn = data.get("inn")
            last_name = data.get("last_name")
            middle_name = data.get("middle_name")
            first_name = data.get("first_name")
            department_id = data.get("department_id")
            role = "user"
            company_ogrn = data.get("company_ogrn")
            schedule_id = 0
            password = generate_password_hash(data.get("password"))
            cur.execute(
                "INSERT INTO public.users (inn, last_name, middle_name, first_name, department_id, role, company_ogrn, schedule_id, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",
                (inn, last_name, middle_name, first_name, department_id, role, company_ogrn, schedule_id, password)
            )
            conn.commit()
            return jsonify(message="OK"), 200
        else:
            return jsonify(error="NOT JSON"), 400
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400
