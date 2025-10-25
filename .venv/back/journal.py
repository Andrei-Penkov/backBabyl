from flask import Blueprint, request, jsonify
from flask import Response, json, current_app
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from collections import OrderedDict
from functools import wraps
from .db import conn, cur

journal_bp = Blueprint('journal_bp', __name__)

@journal_bp.route('/put', methods=['PUT'])
def put_journal_entry():
    try:
        if request.is_json:
            data = request.get_json()
            id = data.get("id")
            start = data.get("start")
            stop = data.get("stop")
            pause = data.get("pause")
            date = data.get("date")
            status = data.get("status")
            note = data.get("note")
            user_inn = data.get("user_inn")
            user_company_ogrn = data.get("user_company_ogrn")
            user_schedule_id = data.get("user_schedule_id")
            cur.execute(
                """INSERT INTO public.journal
                (id, start_time, stop_time, pause, date, status, note, User_INN, User_Company_OGRN, User_Schedule_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                (id, start, stop, pause, date, status, note, user_inn, user_company_ogrn, user_schedule_id)
            )
            conn.commit()
            return jsonify(message="OK"), 200
        else:
            return jsonify(error="NOT JSON"), 400
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400
