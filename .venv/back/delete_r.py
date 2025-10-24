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
    cur.execute("SELECT * FROM public.users WHERE inn = %s", (user_id,))
    rows = cur.fetchall()
    if not len(rows):
        return jsonify({"msg": f"User {user_id} not found"}), 404
    cur.execute('DELETE FROM users WHERE INN = %s', (user_id,))
    conn.commit()
    return jsonify({"msg": f"User {user_id} deleted successfully"}), 200

@del_bp.route('/company/<int:ogrn>', methods=['DELETE'])
def delete_company(ogrn):
    cur.execute("SELECT * FROM public.company WHERE ogrn = %s", (ogrn,))
    rows = cur.fetchall()
    if not len(rows):
        return jsonify({"msg": f"Company {ogrn} not found"}), 404
    cur.execute('DELETE FROM company WHERE OGRN = %s', (ogrn,))
    conn.commit()
    return jsonify({"msg": f"Company {ogrn} deleted successfully"}), 200

@del_bp.route('/journal/<int:id>', methods=['DELETE'])
def delete_journal_note(id):
    cur.execute("SELECT * FROM public.journal WHERE id = %s", (id,))
    rows = cur.fetchall()
    if not len(rows):
        return jsonify({"msg": f"Note with {id} not found"}), 404
    cur.execute('DELETE FROM journal WHERE id = %s', (id,))
    conn.commit()
    return jsonify({"msg": f"Journal note {id} deleted successfully"}), 200

@dis_bp.route('/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    cur.execute("DELETE FROM public.schedule WHERE id = %s;", (schedule_id,))
    conn.commit()
    return jsonify(message="Schedule deleted"), 200
