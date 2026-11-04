import mysql.connector
from flask import current_app, g

def get_db():
    if "db" not in g or not g.db.is_connected():
        g.db = mysql.connector.connect(**current_app.config["DB_CONFIG"])
    return g.db

def query(sql, params=(), one=False):
    cur = get_db().cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows

def execute(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def close_db(error=None):
    conn = g.pop("db", None)
    if conn and conn.is_connected():
        conn.close()
