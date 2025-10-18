from flask import Blueprint, request, jsonify
from flask import Response, json, current_app
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from collections import OrderedDict
from functools import wraps
from .db import conn, cur

dis_bp = Blueprint('dis_bp', __name__)

def UserInfo(row):
    user = {}
    user["inn"] = row[0]
    user["last_name"] = row[1]
    user["first_name"] = row[3]
    user["middle_name"] = row[2]
    user["department_id"] = row[4]
    user["role"] = row[5]
    user["company_ogrn"] = row[6]
    user["schedule_id"] = row[7]
    return user

@dis_bp.route('/users')
def get_users():
    cur.execute("SELECT * FROM public.users;")
    rows = cur.fetchall()
    users = [UserInfo(row) for row in rows]
    response = current_app.response_class(
        json.dumps(users, sort_keys=False),
        mimetype='application/json'
    )
    return response