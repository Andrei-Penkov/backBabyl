from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from .db import conn, cur, get_cursor

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
        cur = get_cursor()
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

@auth_bp.route('/login', methods=['POST'])
def logUser():
    try:
        cur = get_cursor()
        if request.is_json:
            data = request.get_json()
            name = data.get("inn")
            password = data.get("password")
            cur.execute("SELECT password FROM public.users WHERE inn = %s;", (name,))
            rows = cur.fetchall()
            hash = str(rows[0][0])
            if check_password_hash(hash, password):
                cur.execute(
                    f"SELECT * FROM public.users WHERE inn = '{name}'")
                rows = cur.fetchall()
                inn = rows[0][0]
                role = rows[0][5]
                token = create_access_token(identity=name, additional_claims={"role": role})
                return jsonify({"token": token, "role": role, "id": inn}
                               ), 200
            else:
                return jsonify(message="No correct password"), 200
        else:
            return jsonify(error="NOT OK"), 400
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400