# run_init.py
import os
import sys
import getpass
import psycopg2
from psycopg2 import extensions

PG_USER = os.getenv('PGUSER', 'postgres')
PG_PASS = os.getenv('PGPASSWORD')  # try env first
PG_HOST = os.getenv('PGHOST', 'localhost')
PG_PORT = int(os.getenv('PGPORT', 5432))
INIT_SQL = r'C:\coding\sem 6\datwer\database\init.sql'
DB_NAME = 'dwh_gojek'

if not PG_PASS:
    try:
        PG_PASS = getpass.getpass(prompt='Postgres password for user postgres: ')
    except Exception:
        print('Could not read password interactively. Set PGPASSWORD environment variable and retry.')
        sys.exit(1)

def execute_init():
    try:
        # create DB if not exists
        conn = psycopg2.connect(dbname='postgres', user=PG_USER, password=PG_PASS, host=PG_HOST, port=PG_PORT)
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        try:
            cur.execute(f"CREATE DATABASE {DB_NAME};")
        except Exception:
            # ignore if DB exists or cannot create
            pass
        cur.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f'Connection error when creating database: {e}')
        sys.exit(1)

    try:
        # execute init.sql against the new DB
        conn = psycopg2.connect(dbname=DB_NAME, user=PG_USER, password=PG_PASS, host=PG_HOST, port=PG_PORT)
        cur = conn.cursor()
        with open(INIT_SQL, 'r', encoding='utf-8') as f:
            sql_text = f.read()
        cur.execute(sql_text)
        conn.commit()
        cur.close()
        conn.close()
        print('init.sql executed.')
    except psycopg2.OperationalError as e:
        print(f'Connection error when executing init.sql: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'Error executing init.sql: {e}')
        sys.exit(1)

if __name__ == '__main__':
    execute_init()