from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from .db import conn, cur

search_bp = Blueprint('search', __name__)


@search_bp.route('/companies', methods=['GET'])
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