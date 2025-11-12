import psycopg2

def create_connection():
    return psycopg2.connect(
        dbname="backPr",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )

conn = create_connection()

def get_cursor():
    global conn
    try:
        with conn.cursor() as test_cur:
            test_cur.execute("SELECT 1")
    except (OperationalError, InterfaceError):
        conn = create_connection()
    return conn.cursor()

cur = get_cursor()
