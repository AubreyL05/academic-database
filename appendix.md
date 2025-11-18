# Code Appendix
This appendix includes the database schema, complex SQL queries wrapped in Python, CRUD operations, and helper functions used throughout the project.

## Contents
- [Database Schema](#database-schema)
- [Complex Queries](#complex-queries)
- [CRUD Operations](#crud-operations) *(Create, Read, Update, Delete)*
- [DB Helper Functions](#db-helper-functions)

## Database Schema
```SQL
USE student;
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS enrollment;
DROP TABLE IF EXISTS section;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS instructor;
DROP TABLE IF EXISTS student;

CREATE TABLE department (
    department_id INT PRIMARY KEY AUTO_INCREMENT,
    chair_id INT,
    department_name VARCHAR(50) NOT NULL,
    office_location VARCHAR(100)
);

CREATE TABLE student (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    major VARCHAR(100),
    date_of_birth DATE NOT NULL
);

CREATE TABLE instructor (
    instructor_id INT PRIMARY KEY AUTO_INCREMENT,
    department_id INT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    FOREIGN KEY (department_id) REFERENCES department(department_id)
);

CREATE TABLE course (
    course_id INT PRIMARY KEY AUTO_INCREMENT,
    department_id INT,
    course_name VARCHAR(100) NOT NULL,
    course_code VARCHAR(10) NOT NULL,
    credits INT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES department(department_id)
);

CREATE TABLE section (
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
);

CREATE TABLE enrollment (
    enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    section_id INT NOT NULL,
    grade CHAR(2),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (section_id) REFERENCES section(section_id)
);

SET FOREIGN_KEY_CHECKS = 1;
```

## Complex Queries
```python
import db_manager
from pprint import pprint

def get_highest_enrolled_sections():
    """
    Retrieves the course sections with the highest number of enrollments.
    """
    query = """
    SELECT 
        c.course_code, 
        c.course_name, 
        s.section_code,
        COUNT(e.enrollment_id) AS enrollment_count
    FROM 
        section s
    JOIN 
        course c ON s.course_id = c.course_id
    JOIN 
        enrollment e ON s.section_id = e.section_id
    GROUP BY 
        s.section_id, c.course_code, c.course_name, s.section_code
    ORDER BY 
        enrollment_count DESC
    LIMIT 10;
    """
        
    results = db_manager.query_all(query)
    sections = []
    if results:
        for row in results:
            sections.append({
                "course_code": row[0],
                "course_name": row[1],
                "section_code": row[2],
                "enrollment_count": row[3]
            })
    return sections

def get_department_stats():
    """
    Calculates the total number of instructors and courses per department.
    """
    query = """
    SELECT 
        d.department_name, 
        COUNT(DISTINCT i.instructor_id) AS num_instructors,
        COUNT(DISTINCT c.course_id) AS num_courses
    FROM 
        department d
    LEFT JOIN 
        instructor i ON d.department_id = i.department_id
    LEFT JOIN
        course c ON d.department_id = c.department_id
    GROUP BY 
        d.department_name
    ORDER BY 
        num_instructors DESC;
    """
        
    results = db_manager.query_all(query)
    departments = []
    if results:
        for row in results:
            departments.append({
                "department_name": row[0],
                "num_instructors": row[1],
                "num_courses": row[2]
            })
    return departments

def get_students_by_major(major_name: str):
    """
    Finds students enrolled in a specific major.
    """
    query = """
    SELECT 
        first_name, 
        last_name, 
        email
    FROM 
        student
    WHERE 
        major = %s;
    """
    results = db_manager.query_all(query, (major_name,))
        
    return results

def get_top_students_by_gpa(limit=10):
    """
    Returns the top N students by GPA calculated from their enrollments.
    """
    query = """
    SELECT 
        s.student_id,
        s.first_name,
        s.last_name,
        s.major,
        AVG(
            CASE grade
                WHEN 'A' THEN 4.0
                WHEN 'A-' THEN 3.7
                WHEN 'B+' THEN 3.3
                WHEN 'B' THEN 3.0
                WHEN 'B-' THEN 2.7
                WHEN 'C+' THEN 2.3
                WHEN 'C' THEN 2.0
                WHEN 'C-' THEN 1.7
                WHEN 'D+' THEN 1.3
                WHEN 'D' THEN 1.0
                WHEN 'F' THEN 0
                ELSE NULL
            END
        ) AS gpa
    FROM student s
    JOIN enrollment e ON s.student_id = e.student_id
    GROUP BY s.student_id, s.first_name, s.last_name, s.major
    HAVING gpa IS NOT NULL
    ORDER BY gpa DESC
    LIMIT %s;
    """
    results = db_manager.query_all(query, (limit,))
    
    students = []
    if results:
        for row in results:
            students.append({
                "id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "major": row[3],
                "gpa": round(row[4], 2)  # round to 2 decimal places
            })
    return students

def student_transcript(student_id):
    """
    Returns transcript of student with sql and GPA with python using credits and grades
    """
    query = """
    SELECT
        c.course_code,
        c.course_name,
        c.credits,
        s.term,
        s.year,
        e.grade
    FROM enrollment e
    JOIN section s ON s.section_id = e.section_id
    JOIN course c ON c.course_id = s.course_id
    WHERE e.student_id = %s
    ORDER BY s.year, s.term;
    """
    results = db_manager.query_all(query, (student_id,))
    
    student_transcripts = []
    total_points = 0.0
    total_credits = 0.0

    grade_points = {
        'A': 4.0, 'A-': 3.7,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7,
        'D': 1.0, 'F': 0.0
    }

    if results:
        for row in results:
            course_code = row[0]
            course_name = row[1]
            credits = float(row[2])
            term = row[3]
            year = row[4]
            grade = row[5]

            points = grade_points.get(grade)
            if points is not None:
                total_points += points * credits
                total_credits += credits

            student_transcripts.append({
                "course_code": course_code,
                "course_name": course_name,
                "credits": credits,
                "term": term,
                "year": year,
                "grade": grade
            })

    cumulative_gpa = round(total_points / total_credits, 2) if total_credits > 0 else None

    # Attach cumulative GPA to first row or all rows for template
    for row in student_transcripts:
        row["cumulative_gpa"] = cumulative_gpa

    return student_transcripts
```

## CRUD Operations
### Students
```python
# Create
student_id = db_manager.get_length("student") + 1
email = f"john.doe{student_id}@louisville.com"
db_manager.execute(
    "INSERT INTO student (first_name, last_name, email, major, date_of_birth) VALUES (%s,%s,%s,%s,%s)",
    ("John", "Doe", email, "CS", "2000-01-01")
)

# Read
students = db_manager.query_dict("SELECT * FROM student ORDER BY student_id")

# Update
db_manager.execute("UPDATE student SET major=%s WHERE student_id=%s", ("Math", 1))

# Update: Ensure email is unique
email = f"{first.lower()}.{last.lower()}{student_id}@louisville.com"
db_manager.execute(
    "UPDATE student SET email=%s WHERE student_id=%s",
    (email, student_id)
)

# Delete
db_manager.execute("DELETE FROM student WHERE student_id=%s", (1,))
```

### Instructors
```python
# Create
db_manager.execute(
    "INSERT INTO instructor (first_name, last_name, email, department_id) VALUES (%s,%s,%s,%s)",
    ("Jane", "Smith", "jane.smith1@louisville.com", 1)
)

# Read
instructors = db_manager.query_dict("SELECT * FROM instructor ORDER BY instructor_id")

# Update
db_manager.execute("UPDATE instructor SET department_id=%s WHERE instructor_id=%s", (2, 1))

# Delete
db_manager.execute("DELETE FROM instructor WHERE instructor_id=%s", (1,))
```

### Departments
```python
# Create
db_manager.execute(
    "INSERT INTO department (department_name, office_location) VALUES (%s,%s)",
    ("Computer Science", "Room 101")
)

# Read
departments = db_manager.query_dict("SELECT * FROM department ORDER BY department_id")

# Update
db_manager.execute("UPDATE department SET office_location=%s WHERE department_id=%s", ("Room 102", 1))

# Delete
db_manager.execute("DELETE FROM department WHERE department_id=%s", (1,))
```

### Courses
```python
# Create
db_manager.execute(
    "INSERT INTO course (department_id, course_code, course_name, credits) VALUES (%s,%s,%s,%s)",
    (1, "CS101", "Intro to CS", 3)
)

# Read
courses = db_manager.query_dict("SELECT * FROM course ORDER BY course_id")

# Update
db_manager.execute("UPDATE course SET credits=%s WHERE course_id=%s", (4, 1))

# Delete
db_manager.execute("DELETE FROM course WHERE course_id=%s", (1,))
```

### Sections
```python
# Create
db_manager.execute(
    "INSERT INTO section (course_id, instructor_id, section_code, term, year, days, time, capacity, location) "
    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
    (1, 1, "A", "Fall", 2025, "MWF", "09:00-10:00", 30, "Room 201")
)

# Read
sections = db_manager.query_dict("SELECT * FROM section ORDER BY section_id")

# Update
db_manager.execute("UPDATE section SET capacity=%s WHERE section_id=%s", (35, 1))

# Delete
db_manager.execute("DELETE FROM section WHERE section_id=%s", (1,))
```

### Enrollments
```python
# Create
db_manager.execute(
    "INSERT INTO enrollment (student_id, section_id, grade) VALUES (%s,%s,%s)",
    (1, 1, "A")
)

# Read
enrollments = db_manager.query_dict("SELECT * FROM enrollment ORDER BY enrollment_id")

# Update
db_manager.execute("UPDATE enrollment SET grade=%s WHERE enrollment_id=%s", ("A-", 1))

# Delete
db_manager.execute("DELETE FROM enrollment WHERE enrollment_id=%s", (1,))
```

## DB Helper Functions
`db_manager.py`
```python
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
```