import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect
import mysql.connector
import traceback

app = Flask(__name__)
load_dotenv()

# Access database credentials
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

# Connect to DB (your own login) MAKE SURE YOU POPULATE WITH GENERATE_DATA.PY
def get_db():
    try:
        db = mysql.connector.connect(
            host = db_host,
            user = db_user,
            password = db_password,
            database = db_name
        )
        return db
    except Exception as e:
        print("Database connection failed:")
        traceback.print_exc()
        return None

# Home sweet home
@app.route('/')
def index():
    return render_template("index.html")

# Search Builder

def build_search_query(base_query, search_term, search_fields):
    """Adds WHERE conditions for searching across multiple fields."""
    if not search_term:
        return base_query, []
    like_term = f"%{search_term}%"
    conditions = [f"{field} LIKE %s" for field in search_fields]
    where_clause = " WHERE " + " OR ".join(conditions)
    return base_query + where_clause, [like_term] * len(search_fields)

# Students
@app.route('/students')
def students():
    sort = request.args.get('sort', 'student_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '').strip()

    valid_sorts = ['student_id', 'first_name', 'last_name', 'email', 'major', 'date_of_birth']
    if sort not in valid_sorts:
        sort = 'student_id'
    if order not in ['asc', 'desc']:
        order = 'asc'

    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    try:
        cursor = db.cursor(dictionary=True)

        if search:
            query = f"""
                SELECT * FROM student
                WHERE first_name LIKE %s
                   OR last_name LIKE %s
                   OR email LIKE %s
                ORDER BY {sort} {order}
            """
            cursor.execute(query, tuple(['%' + search + '%'] * 3))
        else:
            query = f"SELECT * FROM student ORDER BY {sort} {order}"
            cursor.execute(query)

        data = cursor.fetchall()
        cursor.close()
        db.close()

        return render_template("students/students.html",
                               students=data, sort=sort, order=order, search=search)
    except Exception:
        traceback.print_exc()
        return "<h2>Database query failed.</h2>", 500

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = f"{first_name.lower()}.{last_name.lower()}{get_length("student") + 1}@louisville.com"
            major = request.form.get('major')
            dob = request.form['date_of_birth']

            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO student (first_name, last_name, email, major, date_of_birth)
                VALUES (%s, %s, %s, %s, %s)
            """, (first_name, last_name, email, major, dob))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/students')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database insertion failed.</h2>", 500

    return render_template("students/add_student.html")


@app.route('/delete_student', methods=['GET', 'POST'])
def delete_student():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    if request.method == 'POST':
        student_id = request.form['student_id']
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM enrollment WHERE student_id = %s", (student_id,))
            cursor.execute("DELETE FROM student WHERE student_id = %s", (student_id,))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/students')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database deletion failed.</h2>", 500

    return render_template("students/delete_student.html")

# Instructors
@app.route('/instructors')
def instructors():
    sort = request.args.get('sort', 'instructor_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '').strip()

    valid_sorts = ['instructor_id', 'first_name', 'last_name', 'email', 'department_name']
    if sort not in valid_sorts:
        sort = 'instructor_id'

    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500
    try:
        cursor = db.cursor(dictionary=True)
        base_query = """
            SELECT i.instructor_id, i.first_name, i.last_name, i.email, d.department_name
            FROM instructor i
            LEFT JOIN department d ON i.department_id = d.department_id
        """
        query, params = build_search_query(base_query, search, 
                                           ['i.first_name', 'i.last_name', 'i.email', 'd.department_name'])
        query += f" ORDER BY {sort} {order.upper()}"
        cursor.execute(query, params)
        data = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template("instructors/instructors.html",
                               instructors=data, sort=sort, order=order, search=search)
    except Exception:
        traceback.print_exc()
        return "<h2>Database query failed.</h2>", 500

@app.route('/add_instructor', methods=['GET', 'POST'])
def add_instructor():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    if request.method == 'POST':
        try:
            first = request.form['first_name']
            last = request.form['last_name']
            dept = request.form['department_id']
            email = f"{first.lower()}.{last.lower()}{dept}@louisville.com"

            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO instructor (first_name, last_name, email, department_id)
                VALUES (%s, %s, %s, %s)
            """, (first, last, email, dept))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/instructors')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database insertion failed.</h2>", 500

    return render_template("instructors/add_instructor.html")

@app.route('/delete_instructor', methods=['GET', 'POST'])
def delete_instructor():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    if request.method == 'POST':
        instructor_id = request.form['instructor_id']
        try:
            cursor = db.cursor()

            # Nullify department chairs who reference this instructor
            cursor.execute("UPDATE department SET chair_id = NULL WHERE chair_id = %s", (instructor_id,))
            # Nullify instructor_id section references
            cursor.execute("UPDATE section SET instructor_id = NULL WHERE instructor_id = %s", (instructor_id,))
            # Delete instructor
            cursor.execute("DELETE FROM instructor WHERE instructor_id = %s", (instructor_id,))

            db.commit()
            cursor.close()
            db.close()
            return redirect('/instructors')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database deletion failed.</h2>", 500

    return render_template("instructors/delete_instructor.html")

# Courses
@app.route('/courses')
def courses():
    sort = request.args.get('sort', 'course_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')

    valid_sorts = ['course_id', 'course_code', 'course_name', 'credits', 'department_name']
    if sort not in valid_sorts:
        sort = 'course_id'

    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500
    try:
        cursor = db.cursor(dictionary=True)
        query = f"""
            SELECT c.course_id, c.course_code, c.course_name, c.credits, d.department_name
            FROM course c
            LEFT JOIN department d ON c.department_id = d.department_id
            WHERE c.course_name LIKE %s OR c.course_code LIKE %s
            ORDER BY {sort} {order.upper()}
        """
        cursor.execute(query, (f"%{search}%", f"%{search}%"))
        data = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template("courses/courses.html", courses=data, sort=sort, order=order, search=search)
    except Exception:
        traceback.print_exc()
        return "<h2>Database query failed.</h2>", 500

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    if request.method == 'POST':
        try:
            dept_id = request.form['department_id']
            code = request.form['course_code']
            name = request.form['course_name']
            credits = request.form['credits']

            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO course (department_id, course_code, course_name, credits)
                VALUES (%s, %s, %s, %s)
            """, (dept_id, code, name, credits))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/courses')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database insertion failed.</h2>", 500

    return render_template("courses/add_course.html")

@app.route('/delete_course', methods=['GET', 'POST'])
def delete_course():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    if request.method == 'POST':
        course_id = request.form['course_id']
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM section WHERE course_id = %s", (course_id,))
            cursor.execute("DELETE FROM course WHERE course_id = %s", (course_id,))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/courses')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database deletion failed.</h2>", 500

    return render_template("courses/delete_course.html")

# Departments
@app.route('/departments')
def departments():
    sort = request.args.get('sort', 'department_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500
    try:
        cursor = db.cursor(dictionary=True)
        query = f"""
            SELECT d.department_id, d.department_name, d.office_location,
                   CONCAT(i.first_name, ' ', i.last_name) AS chair_name
            FROM department d
            LEFT JOIN instructor i ON d.chair_id = i.instructor_id
            WHERE d.department_name LIKE %s OR d.office_location LIKE %s
            ORDER BY {sort} {order.upper()}
        """
        cursor.execute(query, (f"%{search}%", f"%{search}%"))
        data = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template("departments/departments.html", departments=data, sort=sort, order=order, search=search)
    except Exception:
        traceback.print_exc()
        return "<h2>Database query failed.</h2>", 500

@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    if request.method == 'POST':
        name = request.form['department_name']
        office = request.form['office_location']

        try:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO department (department_name, office_location)
                VALUES (%s, %s)
            """, (name, office))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/departments')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database insertion failed.</h2>", 500

    return render_template("departments/add_department.html")

@app.route('/delete_department', methods=['GET', 'POST'])
def delete_department():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    if request.method == 'POST':
        dept_id = request.form['department_id']
        try:
            cursor = db.cursor()

            # Nullify instructors in that department first
            cursor.execute("UPDATE instructor SET department_id = NULL WHERE department_id = %s", (dept_id,))

            # Delete department
            cursor.execute("DELETE FROM department WHERE department_id = %s", (dept_id,))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/departments')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database deletion failed.</h2>", 500

    return render_template("departments/delete_department.html")

# Sections
@app.route('/sections')
def sections():
    sort = request.args.get('sort', 'section_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500
    try:
        cursor = db.cursor(dictionary=True)
        query = f"""
            SELECT s.section_id, c.course_code, s.section_code, s.term, s.year,
                   s.days, s.time, s.location,
                   CONCAT(i.first_name, ' ', i.last_name) AS instructor
            FROM section s
            JOIN course c ON s.course_id = c.course_id
            JOIN instructor i ON s.instructor_id = i.instructor_id
            WHERE s.section_code LIKE %s OR c.course_code LIKE %s
                  OR CONCAT(i.first_name, ' ', i.last_name) LIKE %s
            ORDER BY {sort} {order.upper()}
        """
        cursor.execute(query, (f"%{search}%", f"%{search}%", f"%{search}%"))
        data = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template("sections/sections.html", sections=data, sort=sort, order=order, search=search)
    except Exception:
        traceback.print_exc()
        return "<h2>Database query failed.</h2>", 500

@app.route('/add_section', methods=['GET', 'POST'])
def add_section():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500
    if request.method == 'POST':
        try:
            course_id = request.form['course_id']
            instructor_id = request.form['instructor_id']
            code = request.form['section_code']
            term = request.form['term']
            year = request.form['year']
            days = request.form['days']
            time = request.form['time']
            capacity = request.form['capacity']
            location = request.form['location']

            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO section (course_id, instructor_id, section_code, term, year, days, time, capacity, location)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (course_id, instructor_id, code, term, year, days, time, capacity, location))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/sections')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database insertion failed.</h2>", 500
    return render_template("sections/add_section.html")

@app.route('/delete_section', methods=['GET', 'POST'])
def delete_section():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500
    if request.method == 'POST':
        section_id = request.form['section_id']
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM enrollment WHERE section_id = %s", (section_id,))
            cursor.execute("DELETE FROM section WHERE section_id = %s", (section_id,))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/sections')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database deletion failed.</h2>", 500
    return render_template("sections/delete_section.html")

# Enrollments
@app.route('/enrollments')
def enrollments():
    sort = request.args.get('sort', 'enrollment_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500
    try:
        cursor = db.cursor(dictionary=True)
        query = f"""
            SELECT e.enrollment_id,
                   CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                   c.course_code, c.course_name, e.grade
            FROM enrollment e
            JOIN student s ON e.student_id = s.student_id
            JOIN section se ON e.section_id = se.section_id
            JOIN course c ON se.course_id = c.course_id
            WHERE CONCAT(s.first_name, ' ', s.last_name) LIKE %s
               OR c.course_code LIKE %s OR c.course_name LIKE %s
            ORDER BY {sort} {order.upper()}
        """
        cursor.execute(query, (f"%{search}%", f"%{search}%", f"%{search}%"))
        data = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template("enrollments/enrollments.html", enrollments=data, sort=sort, order=order, search=search)
    except Exception:
        traceback.print_exc()
        return "<h2>Database query failed.</h2>", 500

@app.route('/add_enrollment', methods=['GET', 'POST'])
def add_enrollment():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500
    if request.method == 'POST':
        try:
            student_id = request.form['student_id']
            section_id = request.form['section_id']
            grade = request.form['grade']
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO enrollment (student_id, section_id, grade)
                VALUES (%s, %s, %s)
            """, (student_id, section_id, grade))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/enrollments')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database insertion failed.</h2>", 500
    return render_template("enrollments/add_enrollment.html")

@app.route('/delete_enrollment', methods=['GET', 'POST'])
def delete_enrollment():
    db = get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500
    if request.method == 'POST':
        enrollment_id = request.form['enrollment_id']
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM enrollment WHERE enrollment_id = %s", (enrollment_id,))
            db.commit()
            cursor.close()
            db.close()
            return redirect('/enrollments')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database deletion failed.</h2>", 500
    return render_template("enrollments/delete_enrollment.html")

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

# RUN FLASK SERVER 
if __name__ == '__main__':
    print("Flask server starting...")
    app.run(debug=True)
