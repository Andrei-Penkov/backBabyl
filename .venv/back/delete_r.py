from flask import Blueprint, request, jsonify
from flask import Response, json, current_app
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from collections import OrderedDict
from functools import wraps
from .db import conn, cur

del_bp = Blueprint('del_bp', __name__)



@del_bp.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    cur.execute("SELECT * FROM public.users;")
    rows = cur.fetchall()
    if not len(rows):
        return jsonify({"msg": f"User {user_id} not found"}), 404
    cur.execute('DELETE FROM users WHERE INN = %s', (user_id,))
    conn.commit()
    return jsonify({"msg": f"User {user_id} deleted successfully"}), 200
