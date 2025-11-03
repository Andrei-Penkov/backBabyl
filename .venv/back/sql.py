from flask import Blueprint, jsonify
from .db import conn, cur

sql_bp = Blueprint('sql_bp', __name__)

@sql_bp.route('/sql')
def sql():
    try:
        cur.execute(
            '''
            CREATE TABLE Company (
                OGRN integer NOT NULL,
                name text NOT NULL,
                CONSTRAINT Company_PK PRIMARY KEY (OGRN)
            );
            
            CREATE TABLE Schedule (
                id integer NOT NULL,
                start time NOT NULL,
                stop time NOT NULL,
                pause time NOT NULL,
                free boolean NOT NULL,
                CONSTRAINT Schedule_PK PRIMARY KEY (id)
            );
            
            CREATE TABLE Users (
                INN integer NOT NULL,
                last_name text NOT NULL,
                middle_name text NOT NULL,
                first_name text NOT NULL,
                department_id integer NOT NULL,
                role text NOT NULL,
                Company_OGRN integer NOT NULL,
                Schedule_id integer NOT NULL,
                password text NOT NULL,
                CONSTRAINT User_PK PRIMARY KEY (INN),
                CONSTRAINT User_Company_FK FOREIGN KEY (Company_OGRN) REFERENCES Company(OGRN) ON DELETE CASCADE ON UPDATE CASCADE,
                CONSTRAINT User_Schedule_FK FOREIGN KEY (Schedule_id) REFERENCES Schedule(id) ON DELETE CASCADE ON UPDATE CASCADE
            );
            
            CREATE TABLE Journal (
                id integer NOT NULL,
                start_time time NOT NULL,
                stop_time time NOT NULL,
                pause time NOT NULL,
                date date NOT NULL,
                status text NOT NULL,
                note text,
                User_INN integer NOT NULL,
                User_Company_OGRN integer NOT NULL,
                User_Schedule_id integer NOT NULL,
                CONSTRAINT Journal_PK PRIMARY KEY (id),
                CONSTRAINT Journal_User_FK FOREIGN KEY (User_INN) REFERENCES Users(INN) ON DELETE CASCADE ON UPDATE CASCADE
            );
            '''
        )
        conn.commit()
        return jsonify(message="OK"), 200
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400


@sql_bp.route('/sqldel')
def sqldel():
    try:
        cur.execute('DROP TABLE Journal, Users, Schedule, Company CASCADE;')
        conn.commit()
        return jsonify(message="OK"), 200
    except Exception as e:
        conn.rollback()
        return jsonify(message=f"NOT OK {e}"), 400
