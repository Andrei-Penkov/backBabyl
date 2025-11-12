from flask import Blueprint, request, jsonify
from flask import Response, json, current_app
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from collections import OrderedDict
from functools import wraps
from .db import conn, cur, get_cursor
from .auth import role_required

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
@role_required(['admin', 'moderator','user'])
def get_users():
    try:
        cur = get_cursor()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

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

        allowed_params = set(search_fields.keys()) | {'page', 'per_page'}

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

        total_count = 0

        if not search_params:

            base_query = "SELECT * FROM public.users ORDER BY last_name, first_name"
            paginated_query = paginate_query(base_query, page, per_page)
            cur.execute(paginated_query)
            rows = cur.fetchall()
            rez = [UserInfo(row) for row in rows]


            cur.execute("SELECT COUNT(*) FROM public.users")
            total_count = cur.fetchone()[0]
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


                base_query = f"SELECT * FROM public.users WHERE {where_clause} ORDER BY last_name, first_name"
                paginated_query = paginate_query(base_query, page, per_page)
                cur.execute(paginated_query, values)

                for row in cur.fetchall():
                    rez.append(UserInfo(row))


                count_query = f"SELECT COUNT(*) FROM public.users WHERE {where_clause}"
                cur.execute(count_query, values)
                total_count = cur.fetchone()[0]

        seen = set()
        unique_rez = []
        for item in rez:
            item_key = tuple(sorted(item.items()))
            if item_key not in seen:
                seen.add(item_key)
                unique_rez.append(item)
        rez = unique_rez


        response_data = {
            'data': rez,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            },
            'count': len(rez)
        }

        response = current_app.response_class(
            json.dumps(response_data, sort_keys=False, ensure_ascii=False),
            mimetype='application/json'
        )
        return response
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400


@dis_bp.route('/jour', methods=['GET'])
@role_required(['admin', 'moderator','user'])
def get_journal_entries():
    try:
        cur = get_cursor()
        search_fields = {
            'id': 'id = %s',
            'start_time': 'start_time::TEXT LIKE %s',
            'stop_time': 'stop_time::TEXT LIKE %s',
            'pause': 'pause::TEXT LIKE %s',
            'date': 'date = %s',
            'status': 'LOWER(status) LIKE LOWER(%s)',
            'note': 'LOWER(note) LIKE LOWER(%s)',
            'user_inn': 'User_INN = %s',
            'user_company_ogrn': 'User_Company_OGRN = %s',
            'user_schedule_id': 'User_Schedule_id = %s'
        }


        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)


        all_request_params = set(request.args.keys())
        allowed_params = set(search_fields.keys()) | {'page', 'per_page'}
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


        if search_params:
            from itertools import product

            param_combinations = []
            for field, field_values in search_params.items():
                param_combinations.append([(field, value) for value in field_values])

            all_combinations = product(*param_combinations)
            all_entries = []

            for combination in all_combinations:
                combo_conditions = []
                combo_values = []

                for field, value in combination:
                    condition = search_fields[field]
                    if 'LIKE' in condition:
                        combo_values.append(f'%{value}%')
                    else:
                        try:

                            if field in ['id', 'user_inn', 'user_company_ogrn', 'user_schedule_id']:
                                combo_values.append(int(value))
                            # Дата
                            elif field == 'date':
                                combo_values.append(value)
                            else:
                                combo_values.append(value)
                        except ValueError:
                            combo_values.append(value)

                    combo_conditions.append(condition)

                where_clause = " AND ".join(combo_conditions)
                base_query = f"SELECT * FROM public.journal WHERE {where_clause} ORDER BY date DESC, id DESC"


                paginated_query = paginate_query(base_query, page, per_page)
                cur.execute(paginated_query, combo_values)

                for row in cur.fetchall():
                    all_entries.append(JournalEntry(row))


            seen = set()
            entries = []
            for item in all_entries:
                item_key = tuple(sorted(item.items()))
                if item_key not in seen:
                    seen.add(item_key)
                    entries.append(item)

            total_where_conditions = []
            total_values = []
            for field, field_values in search_params.items():
                condition = search_fields[field]
                field_conditions = []
                for value in field_values:
                    if 'LIKE' in condition:
                        total_values.append(f'%{value}%')
                    else:
                        try:
                            if field in ['id', 'user_inn', 'user_company_ogrn', 'user_schedule_id']:
                                total_values.append(int(value))
                            elif field == 'date':
                                total_values.append(value)
                            else:
                                total_values.append(value)
                        except ValueError:
                            total_values.append(value)
                    field_conditions.append(condition)

                total_where_conditions.append(f"({' OR '.join(field_conditions)})")

            total_where_clause = " AND ".join(total_where_conditions)
            count_query = f"SELECT COUNT(*) FROM public.journal WHERE {total_where_clause}"
            cur.execute(count_query, total_values)
            total = cur.fetchone()[0]

        else:
            base_query = "SELECT * FROM public.journal ORDER BY date DESC, id DESC"
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
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400

@dis_bp.route('/sch', methods=['GET'])
@role_required(['admin', 'moderator','user'])
def get_schedules():
    try:
        cur = get_cursor()
        search_fields = {
            'free': 'free = %s'
        }

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        all_request_params = set(request.args.keys())
        allowed_params = set(search_fields.keys()) | {'page', 'per_page'}
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

        if search_params:
            from itertools import product

            param_combinations = []
            for field, field_values in search_params.items():
                param_combinations.append([(field, value) for value in field_values])

            all_combinations = product(*param_combinations)
            all_entries = []

            for combination in all_combinations:
                combo_conditions = []
                combo_values = []

                for field, value in combination:
                    condition = search_fields[field]
                    combo_values.append(value)
                    combo_conditions.append(condition)

                where_clause = " AND ".join(combo_conditions)
                base_query = f"SELECT * FROM public.schedule WHERE {where_clause} ORDER BY id DESC"

                paginated_query = paginate_query(base_query, page, per_page)
                cur.execute(paginated_query, combo_values)

                for row in cur.fetchall():
                    all_entries.append(ScheduleEntry(row))

            seen = set()
            entries = []
            for item in all_entries:
                item_key = tuple(sorted(item.items()))
                if item_key not in seen:
                    seen.add(item_key)
                    entries.append(item)

            total_where_conditions = []
            total_values = []
            for field, field_values in search_params.items():
                condition = search_fields[field]
                field_conditions = []
                for value in field_values:
                    total_values.append(value)
                    field_conditions.append(condition)

                total_where_conditions.append(f"({' OR '.join(field_conditions)})")

            total_where_clause = " AND ".join(total_where_conditions)
            count_query = f"SELECT COUNT(*) FROM public.schedule WHERE {total_where_clause}"
            cur.execute(count_query, total_values)
            total = cur.fetchone()[0]

        else:
            base_query = "SELECT * FROM public.schedule ORDER BY id DESC"
            paginated_query = paginate_query(base_query, page, per_page)
            cur.execute(paginated_query)
            rows = cur.fetchall()
            entries = [ScheduleEntry(row) for row in rows]

            cur.execute("SELECT COUNT(*) FROM public.schedule")
            total = cur.fetchone()[0]

        return jsonify({
            "schedules": entries,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400



@dis_bp.route('/companies', methods=['GET'])
@role_required(['admin', 'moderator','user'])
def search_companies():
    try:
        cur = get_cursor()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        search_name = request.args.get('name')
        search_ogrn = request.args.get('ogrn')

        rez = []

        allowed_params = {'name', 'ogrn', 'page', 'per_page'}
        invalid_params = set(request.args.keys()) - allowed_params

        if invalid_params:
            return jsonify({
                "error": "Недопустимые параметры поиска",
                "invalid_params": list(invalid_params),
                "allowed_params": list(allowed_params)
            }), 400

        if search_name and search_ogrn:
            names = search_name.split('_')
            ogrns = search_ogrn.split('_')

            for name in names:
                for ogrn in ogrns:

                    base_query = """
                        SELECT * FROM public.Company 
                        WHERE LOWER(name) LIKE LOWER(%s) 
                        AND OGRN::TEXT LIKE %s
                        ORDER BY name
                    """
                    paginated_query = paginate_query(base_query, page, per_page)
                    cur.execute(paginated_query, (f'%{name}%', f'%{ogrn}%'))
                    rows = cur.fetchall()
                    for row in rows:
                        rez.append({
                            'ogrn': row[0],
                            'name': row[1]
                        })


                    count_query = """
                        SELECT COUNT(*) FROM public.Company 
                        WHERE LOWER(name) LIKE LOWER(%s) 
                        AND OGRN::TEXT LIKE %s
                    """
                    cur.execute(count_query, (f'%{name}%', f'%{ogrn}%'))


        elif search_name is not None:
            names = search_name.split('_')
            for name in names:

                base_query = "SELECT * FROM public.Company WHERE LOWER(name) LIKE LOWER(%s) ORDER BY name"
                paginated_query = paginate_query(base_query, page, per_page)
                cur.execute(paginated_query, (f'%{name}%',))
                rows = cur.fetchall()
                for row in rows:
                    rez.append({
                        'ogrn': row[0],
                        'name': row[1]
                    })


                count_query = "SELECT COUNT(*) FROM public.Company WHERE LOWER(name) LIKE LOWER(%s)"
                cur.execute(count_query, (f'%{name}%',))


        elif search_ogrn is not None:
            ogrns = search_ogrn.split('_')
            for ogrn in ogrns:

                base_query = "SELECT * FROM public.Company WHERE OGRN::TEXT LIKE %s ORDER BY name"
                paginated_query = paginate_query(base_query, page, per_page)
                cur.execute(paginated_query, (f'%{ogrn}%',))
                rows = cur.fetchall()
                for row in rows:
                    rez.append({
                        'ogrn': row[0],
                        'name': row[1]
                    })


                count_query = "SELECT COUNT(*) FROM public.Company WHERE OGRN::TEXT LIKE %s"
                cur.execute(count_query, (f'%{ogrn}%',))


        else:

            base_query = "SELECT * FROM public.Company ORDER BY name"
            paginated_query = paginate_query(base_query, page, per_page)
            cur.execute(paginated_query)
            rows = cur.fetchall()
            for row in rows:
                rez.append({
                    'ogrn': row[0],
                    'name': row[1]
                })


            cur.execute("SELECT COUNT(*) FROM public.Company")
            total_count = cur.fetchone()[0]


        rez = [dict(t) for t in {frozenset(d.items()) for d in rez}]


        return jsonify({
            "data": rez,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            },
            "count": len(rez)
        })
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400