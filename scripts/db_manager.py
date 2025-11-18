# shortened, reusable DB helpers
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_db():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
    except Exception:
        return None

def query_all(query, params=None, dict_mode=False):
    db = get_db()
    if not db:
        return None
    try:
        cursor = db.cursor(dictionary=dict_mode, buffered=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except Exception as e:
        print("DB ERROR:", e)
        return None
    finally:
        try:
            db.close()
        except Exception:
            pass

def query_dict(query, params=None):
    return query_all(query, params, dict_mode=True)

def execute(query, params=None):
    """Run a single modifying statement (INSERT/UPDATE/DELETE). Returns True on success."""
    db = get_db()
    if not db:
        return False
    try:
        cursor = db.cursor()
        cursor.execute(query, params or ())
        db.commit()
        return True
    except Exception as e:
        print("DB EXEC ERROR:", e)
        try:
            db.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            db.close()
        except Exception:
            pass

def get_length(table: str):
    res = query_all(f"SELECT COUNT(*) FROM {table}")
    return res[0][0] if res and len(res) and isinstance(res[0], (list, tuple)) else 0