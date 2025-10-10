from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps

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

# Надо добавить сюда регистрацию и логин
