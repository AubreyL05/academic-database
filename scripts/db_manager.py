import mysql.connector
from dotenv import load_dotenv
import os

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
    
def fetch_all(query: str, params: tuple = None):
    """Executes a SELECT query and returns all matching rows."""
    db = get_db()
    if db is None:
        return None

    try:
        # Use buffered cursor to fetch all results immediately
        cursor = db.cursor(buffered=True) 
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
    finally:
        if db and db.is_connected():
            db.close()

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

def reset_tables():
    db = get_db()
    cursor = db.cursor()

    sql_commands = [
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

    try:
        for cmd in sql_commands:
            cursor.execute(cmd)

        db.commit()
        return "Tables successfully reset."

    except Exception as e:
        db.rollback()
        return f"Error resetting tables: {e}"