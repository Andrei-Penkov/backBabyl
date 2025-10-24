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

@dis_bp.route('/companies', methods=['GET'])
def search_companies():
    search_name = request.args.get('name')
    search_ogrn = request.args.get('ogrn')

    rez = []


    if search_name and search_ogrn:
        names = search_name.split('_')
        ogrns = search_ogrn.split('_')

        for name in names:
            for ogrn in ogrns:
                cur.execute("""
                    SELECT * FROM public.Company 
                    WHERE LOWER(name) LIKE LOWER(%s) 
                    AND OGRN::TEXT LIKE %s;
                """, (f'%{name}%', f'%{ogrn}%'))
                rows = cur.fetchall()
                for row in rows:
                    rez.append({
                        'ogrn': row[0],
                        'name': row[1]
                    })

    elif search_name is not None:
        names = search_name.split('_')
        for name in names:
            cur.execute("SELECT * FROM public.Company WHERE LOWER(name) LIKE LOWER(%s);",
                        (f'%{name}%',))
            rows = cur.fetchall()
            for row in rows:
                rez.append({
                    'ogrn': row[0],
                    'name': row[1]
                })

    elif search_ogrn is not None:
        ogrns = search_ogrn.split('_')
        for ogrn in ogrns:
            cur.execute("SELECT * FROM public.Company WHERE OGRN::TEXT LIKE %s;",
                        (f'%{ogrn}%',))
            rows = cur.fetchall()
            for row in rows:
                rez.append({
                    'ogrn': row[0],
                    'name': row[1]
                })

    else:
        cur.execute("SELECT * FROM public.Company ORDER BY name;")
        rows = cur.fetchall()
        for row in rows:
            rez.append({
                'ogrn': row[0],
                'name': row[1]
            })

    rez = [dict(t) for t in {frozenset(d.items()) for d in rez}]
    return jsonify(rez)