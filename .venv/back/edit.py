from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from .db import conn, cur

edit_bp = Blueprint('edit', __name__)

@edit_bp.route('/company', methods=['PATCH'])
def edit_company():
    try:
        if not request.is_json:
            return jsonify(error="NOT JSON"), 400

        data = request.get_json()
        ogrn = data.get("ogrn")          # текущий ogrn для поиска записи
        new_orgn = data.get("new_orgn")  # новое ogrn для обновления, если вдруг компания при регистрации ошиблась с ogrn
        new_name = data.get("new_name")  # новое имя компании, если вдруг компания захочет поменять имя

        if not ogrn:
            return jsonify(error="Missing ogrn"), 400

        if new_orgn is None and new_name is None:
            return jsonify(error="No fields to update"), 400

        sets = []
        params = []

        if new_orgn is not None:
            sets.append("ogrn = %s")
            params.append(new_orgn)

        if new_name is not None:
            sets.append("name = %s")
            params.append(new_name)

        params.append(ogrn)

        sql = f"UPDATE public.company SET {', '.join(sets)} WHERE ogrn = %s;"

        cur.execute(sql, tuple(params))
        if cur.rowcount == 0:
            return jsonify(error="Company not found"), 404

        conn.commit()
        return jsonify(message="Company updated successfully"), 200

    except Exception as e:
        conn.rollback()
        return jsonify(message=f"Update failed: {e}"), 400
