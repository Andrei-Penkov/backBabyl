from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from .db import conn, cur

add_bp = Blueprint('add', __name__)

@add_bp.route('/company', methods=['POST'])
def add_company():
    try:
        if request.is_json:
            data = request.get_json()
            company_ogrn = data.get("company_ogrn")
            company_name = data.get("name")
            cur.execute(
                "INSERT INTO public.company (ogrn, name) VALUES (%s,%s);",
                (company_ogrn, company_name)
            )
            conn.commit()
            return jsonify(message="OK"), 200
        else:
            return jsonify(error="NOT JSON"), 400
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400