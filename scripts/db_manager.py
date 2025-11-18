import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_db():
    """Establishes connection to database."""
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
    """Executes a SELECT query and fetches all resulting rows."""
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
    """Run a single modifying statement (INSERT/UPDATE/DELETE)."""
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

def execute_many(sql_list_with_params):
    """Execute a list of (sql, params) tuples in one DB transaction."""
    db = get_db()
    if not db:
        return False
    try:
        cursor = db.cursor()
        for sql, params in sql_list_with_params:
            cursor.execute(sql, params or ())
        db.commit()
        return True
    except Exception as e:
        print("DB MULTI ERROR:", e)
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

def reset_tables():
    """Executes table schema, wiping all records."""
    commands = [
        "SET FOREIGN_KEY_CHECKS = 0",
        "DROP TABLE IF EXISTS enrollment",
        "DROP TABLE IF EXISTS section",
        "DROP TABLE IF EXISTS course",
        "DROP TABLE IF EXISTS instructor",
        "DROP TABLE IF EXISTS student",
        "DROP TABLE IF EXISTS department",
        """CREATE TABLE department (
            department_id INT PRIMARY KEY AUTO_INCREMENT,
            chair_id INT,
            department_name VARCHAR(50) NOT NULL,
            office_location VARCHAR(100)
        )""",
        """CREATE TABLE student (
            student_id INT PRIMARY KEY AUTO_INCREMENT,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            major VARCHAR(100),
            date_of_birth DATE NOT NULL
        )""",
        """CREATE TABLE instructor (
            instructor_id INT PRIMARY KEY AUTO_INCREMENT,
            department_id INT,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            FOREIGN KEY (department_id) REFERENCES department(department_id)
        )""",
        """CREATE TABLE course (
            course_id INT PRIMARY KEY AUTO_INCREMENT,
            department_id INT,
            course_name VARCHAR(100) NOT NULL,
            course_code VARCHAR(10) NOT NULL,
            credits INT NOT NULL,
            FOREIGN KEY (department_id) REFERENCES department(department_id)
        )""",
        """CREATE TABLE section (
            section_id INT PRIMARY KEY AUTO_INCREMENT,
            course_id INT NOT NULL,
            instructor_id INT,
            section_code VARCHAR(15) NOT NULL,
            term VARCHAR(10) NOT NULL,
            year INT NOT NULL,
            time VARCHAR(20),
            days VARCHAR(50),
            capacity INT NOT NULL,
            location VARCHAR(50),
            FOREIGN KEY (course_id) REFERENCES course(course_id),
            FOREIGN KEY (instructor_id) REFERENCES instructor(instructor_id)
        )""",
        """CREATE TABLE enrollment (
            enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
            student_id INT NOT NULL,
            section_id INT NOT NULL,
            grade CHAR(2),
            FOREIGN KEY (student_id) REFERENCES student(student_id),
            FOREIGN KEY (section_id) REFERENCES section(section_id)
        )""",
        "SET FOREIGN_KEY_CHECKS = 1"
    ]

    # Execute all
    return execute_many([(cmd, None) for cmd in commands])