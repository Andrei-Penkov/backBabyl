from flask import Blueprint, request, jsonify
from flask import Response, json, current_app
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from collections import OrderedDict
from functools import wraps
from .db import conn, cur

dis_bp = Blueprint('dis_bp', __name__)

def paginate_query(query, page, per_page):
    offset = (page - 1) * per_page
    query = query + f" LIMIT {per_page} OFFSET {offset}"
    return query

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

def JournalEntry(row):
    return {
        "id": row[0],
        "start_time": str(row[1]),
        "stop_time": str(row[2]),
        "pause": str(row[3]),
        "date": row[4].isoformat(),
        "status": row[5],
        "note": row[6],
        "user_inn": row[7],
        "user_company_ogrn": row[8],
        "user_schedule_id": row[9]
    }

def ScheduleEntry(row):
    return {
        "id": row[0],
        "start": str(row[1]),
        "stop": str(row[2]),
        "pause": str(row[3]),
        "free": row[4]
    }


@dis_bp.route('/users', methods=['GET'])
def get_users():
    search_fields = {
        'inn': 'INN = %s',
        'last_name': 'LOWER(last_name) LIKE LOWER(%s)',
        'first_name': 'LOWER(first_name) LIKE LOWER(%s)',
        'middle_name': 'LOWER(middle_name) LIKE LOWER(%s)',
        'department_id': 'department_id = %s',
        'role': 'LOWER(role) LIKE LOWER(%s)',
        'company_ogrn': 'Company_OGRN = %s',
        'schedule_id': 'Schedule_id = %s'
    }

    all_request_params = set(request.args.keys())


    allowed_params = set(search_fields.keys())


    invalid_params = all_request_params - allowed_params


    if invalid_params:
        return jsonify({
            "error": "Недопустимые параметры поиска",
            "invalid_params": list(invalid_params),
            "allowed_params": list(allowed_params)
        }), 400


    search_params = {}
    for field in search_fields.keys():
        value = request.args.get(field)
        if value:
            search_params[field] = value.split('_')

    if not search_params:
        cur.execute("SELECT * FROM public.users ORDER BY last_name, first_name;")
        rows = cur.fetchall()
        rez = [UserInfo(row) for row in rows]
    else:
        from itertools import product

        param_combinations = []
        for field, values in search_params.items():
            param_combinations.append([(field, value) for value in values])

        all_combinations = product(*param_combinations)
        rez = []

        for combination in all_combinations:
            where_conditions = []
            values = []

            for field, value in combination:
                condition = search_fields[field]
                if 'LIKE' in condition:
                    values.append(f'%{value}%')
                else:
                    try:
                        if field in ['inn', 'department_id', 'company_ogrn', 'schedule_id']:
                            values.append(int(value))
                        else:
                            values.append(value)
                    except ValueError:
                        values.append(value)

                where_conditions.append(condition)

            where_clause = " AND ".join(where_conditions)
            query = f"SELECT * FROM public.users WHERE {where_clause};"
            cur.execute(query, values)

            for row in cur.fetchall():
                rez.append(UserInfo(row))

    seen = set()
    unique_rez = []
    for item in rez:
        item_key = tuple(sorted(item.items()))
        if item_key not in seen:
            seen.add(item_key)
            unique_rez.append(item)
    rez = unique_rez

    response = current_app.response_class(
        json.dumps(rez, sort_keys=False, ensure_ascii=False),
        mimetype='application/json'
    )
    return response

@dis_bp.route('/jour', methods=['GET'])
def get_journal_entries():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    base_query = "SELECT * FROM public.journal ORDER BY date DESC"
    paginated_query = paginate_query(base_query, page, per_page)

    cur.execute(paginated_query)
    rows = cur.fetchall()
    entries = [JournalEntry(row) for row in rows]

    cur.execute("SELECT COUNT(*) FROM public.journal")
    total = cur.fetchone()[0]

    return jsonify({
        "entries": entries,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    })

@dis_bp.route('/sch', methods=['POST'])
def get_schedules():
    data = request.get_json()
    page = data.get("page", 1)
    per_page = data.get("per_page", 10)
    free = data.get("free")

    base_query = "SELECT * FROM public.schedule"
    params = []

    if free is not None:
        base_query += " WHERE free = %s"
        params.append(free)

    base_query += " ORDER BY id DESC"
    paginated_query = paginate_query(base_query, page, per_page)

    cur.execute(paginated_query, tuple(params))
    rows = cur.fetchall()
    schedules = [ScheduleEntry(row) for row in rows]

    count_query = "SELECT COUNT(*) FROM public.schedule"
    if free is not None:
        count_query += " WHERE free = %s"
        cur.execute(count_query, (free,))
    else:
        cur.execute(count_query)

    total = cur.fetchone()[0]

    return jsonify({
        "schedules": schedules,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    })

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