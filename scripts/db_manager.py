import mysql.connector
from dotenv import load_dotenv
import os
import math

load_dotenv()

def get_db():
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")

    try:
        db = mysql.connector.connect(
            host = db_host,
            user = db_user,
            password = db_password,
            database = db_name
        )
        return db
    except Exception:
        return None

def get_length(table: str):
    db = get_db()

    try:
        cursor = db.cursor()

        query = f"SELECT COUNT(*) FROM {table}" 
        cursor.execute(query)
        
        result = cursor.fetchone()
        count = result[0] if result else 0
        cursor.close()
        return count
    finally:
        if db and db.is_connected():
            db.close()