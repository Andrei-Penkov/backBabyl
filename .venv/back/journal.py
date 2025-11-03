from flask import Blueprint, request, jsonify
from flask import Response, json, current_app
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from collections import OrderedDict
from functools import wraps
from .db import conn, cur

journal_bp = Blueprint('journal_bp', __name__)
def paginate_query(query, page, per_page):
    offset = (page - 1) * per_page
    query = query + f" LIMIT {per_page} OFFSET {offset}"
    return query


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


def time_to_minutes(t):
    if t:
        return t.hour * 60 + t.minute + t.second / 60
    return 0



def format_time(t):
    if t:
        return t.strftime('%H:%M')
    return '00:00'


@journal_bp.route('/get', methods=['GET'])
def get_info_journal():
    try:

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        total_count = 0

        search_fields = {
            'date': 'j.date = %s',
            'inn': 'u.INN = %s',
            'department_id': 'u.department_id = %s',
            'company_ogrn': 'u.Company_OGRN = %s',
            'status': 'LOWER(j.status) LIKE LOWER(%s)',
            'last_name': 'LOWER(u.last_name) LIKE LOWER(%s)',
            'first_name': 'LOWER(u.first_name) LIKE LOWER(%s)',
            'middle_name': 'LOWER(u.middle_name) LIKE LOWER(%s)'
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


        base_query = """
        SELECT 
            j.date,
            u.INN,
            u.last_name,
            u.middle_name, 
            u.first_name,
            u.department_id,
            u.Company_OGRN,
            j.start_time,
            s.start,
            j.stop_time,
            s.stop,
            j.pause,
            s.pause,
            j.status,
            j.note
        FROM Journal j
        JOIN Users u ON j.User_INN = u.INN 
            AND j.User_Company_OGRN = u.Company_OGRN 
            AND j.User_Schedule_id = u.Schedule_id
        JOIN Schedule s ON u.Schedule_id = s.id
        """


        count_query = """
        SELECT COUNT(*)
        FROM Journal j
        JOIN Users u ON j.User_INN = u.INN 
            AND j.User_Company_OGRN = u.Company_OGRN 
            AND j.User_Schedule_id = u.Schedule_id
        JOIN Schedule s ON u.Schedule_id = s.id
        """

        response_data = []


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
                            if field in ['inn', 'department_id', 'company_ogrn']:
                                combo_values.append(int(value))
                            else:
                                combo_values.append(value)
                        except ValueError:
                            combo_values.append(value)

                    combo_conditions.append(condition)

                where_clause = " AND ".join(combo_conditions)


                full_query = f"{base_query} WHERE {where_clause} ORDER BY j.date DESC, u.INN"
                paginated_query = paginate_query(full_query, page, per_page)
                cur.execute(paginated_query, combo_values)

                for row in cur.fetchall():
                    all_entries.append(row)


                count_full_query = f"{count_query} WHERE {where_clause}"
                cur.execute(count_full_query, combo_values)



            seen = set()
            for row in all_entries:
                if row not in seen:
                    seen.add(row)
                    response_data.append(row)

        else:

            base_query += " ORDER BY j.date DESC, u.INN"
            paginated_query = paginate_query(base_query, page, per_page)
            cur.execute(paginated_query)
            response_data = cur.fetchall()


            cur.execute(f"SELECT COUNT(*) FROM ({base_query}) as subquery")
            total_count = cur.fetchone()[0]


        formatted_data = []
        for row in response_data:
            date, inn, last_name, middle_name, first_name, department_id, ogrn, \
                journal_start, schedule_start, journal_stop, schedule_stop, \
                journal_pause, schedule_pause, status, note = row


            required_minutes = max(0, time_to_minutes(schedule_stop) -
                                   time_to_minutes(schedule_start) -
                                   time_to_minutes(schedule_pause))

            actual_minutes = max(0, time_to_minutes(journal_stop) -
                                 time_to_minutes(journal_start) -
                                 time_to_minutes(journal_pause))


            entry = {
                'date': date.isoformat() if date else None,
                'inn': inn,
                'last_name': last_name,
                'first_name': first_name,
                'middle_name': middle_name,
                'department_id': department_id,
                'company_ogrn': ogrn,
                'start_time': format_time(journal_start),
                'start': format_time(schedule_start),
                'stop_time': format_time(journal_stop),
                'stop': format_time(schedule_stop),
                'pause_journal': format_time(journal_pause),
                'pause_schedule': format_time(schedule_pause),
                'required_work_minutes': round(required_minutes, 2),
                'actual_work_minutes': round(actual_minutes, 2),
                'status': status,
                'note': note
            }

            formatted_data.append(entry)

        response = Response(
            json.dumps({
                'data': formatted_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                },
                'count': len(formatted_data)
            }, ensure_ascii=False, sort_keys=False),
            mimetype='application/json'
        )

        return response

    except Exception as e:
        conn.rollback()
        return jsonify({
            'error': str(e)
        }), 500