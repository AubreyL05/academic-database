from flask import Flask, render_template, request, redirect, flash, url_for
from generate_data import main as generate_data_main
import traceback, os
import db_manager, complex

app = Flask(__name__)
app.secret_key = os.urandom(24)

def build_search_query(base_query, search_term, fields):
    if not search_term:
        return base_query, None
    like = f"%{search_term}%"
    condition = " OR ".join(f"{f} LIKE %s" for f in fields)
    return base_query + " WHERE " + condition, tuple([like] * len(fields))

@app.route('/students')
def students():
    sort = request.args.get('sort', 'student_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '').strip()

    valid_sorts = ['student_id', 'first_name', 'last_name', 'email', 'major', 'date_of_birth']
    if sort not in valid_sorts:
        sort = 'student_id'

    base = "SELECT * FROM student"
    query, params = build_search_query(base, search, ["first_name", "last_name", "email"])
    query += f" ORDER BY {sort} {order}"

    data = db_manager.query_dict(query, params)
    return render_template("students/students.html", students=data, sort=sort, order=order, search=search)


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    db = db_manager.get_db()
    if not db:
        return "<h2>Could not connect to database.</h2>", 500

    if request.method == 'POST':
        try:
            first = request.form['first_name'].strip()
            last = request.form['last_name'].strip()
            major = request.form.get('major')
            dob = request.form['date_of_birth']
            
            cursor = db.cursor()

            # Count existing students with the same name
            cursor.execute("SELECT COUNT(*) FROM student WHERE first_name = %s AND last_name = %s", (first, last))
            
            existing_count = cursor.fetchone()[0]
            new_suffix_num = existing_count + 1
            suffix = f"{new_suffix_num:02d}"
            
            email = f"{first.lower()}.{last.lower()}{suffix}@louisville.com"
            
            # 3. Insert the new student with the correctly generated email in one go
            cursor.execute("""
                INSERT INTO student (first_name, last_name, email, major, date_of_birth)
                VALUES (%s, %s, %s, %s, %s)
            """, (first, last, email, major, dob))

            db.commit()
            cursor.close()

            return redirect('/students')
        except Exception:
            db.rollback()
            traceback.print_exc()
            return "<h2>Database insertion failed.</h2>", 500

    return render_template("students/add_student.html")


@app.route('/delete_student', methods=['GET', 'POST'])
def delete_student():
    if request.method == 'POST':
        sid = request.form['student_id']
        ok = db_manager.execute("DELETE FROM enrollment WHERE student_id=%s", (sid,)) \
             and db_manager.execute("DELETE FROM student WHERE student_id=%s", (sid,))
        return redirect('/students') if ok else "<h2>Delete failed.</h2>"
    return render_template("students/delete_student.html")

@app.route('/instructors')
def instructors():
    sort = request.args.get('sort', 'instructor_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '').strip()

    valid_sorts = ['instructor_id', 'first_name', 'last_name', 'email', 'department_name']
    if sort not in valid_sorts:
        sort = 'instructor_id'

    base = """
        SELECT i.instructor_id, i.first_name, i.last_name, i.email, d.department_name
        FROM instructor i
        LEFT JOIN department d ON i.department_id = d.department_id
    """

    query, params = build_search_query(base, search,
        ["i.first_name", "i.last_name", "i.email", "d.department_name"])

    query += f" ORDER BY {sort} {order}"
    data = db_manager.query_dict(query, params)
    return render_template("instructors/instructors.html",
                           instructors=data, sort=sort, order=order, search=search)


@app.route('/add_instructor', methods=['GET', 'POST'])
def add_instructor():
    if request.method == 'POST':
        first = request.form['first_name']
        last = request.form['last_name']
        dept = request.form['department_id']
        email = f"{first.lower()}.{last.lower()}@louisville.com"

        ok = db_manager.execute("""
            INSERT INTO instructor (first_name, last_name, email, department_id)
            VALUES (%s,%s,%s,%s)
        """, (first, last, email, dept))

        return redirect('/instructors') if ok else "<h2>Insert failed.</h2>"

    return render_template("instructors/add_instructor.html")


@app.route('/delete_instructor', methods=['GET', 'POST'])
def delete_instructor():
    if request.method == 'POST':
        iid = request.form['instructor_id']

        ok = db_manager.execute("UPDATE department SET chair_id=NULL WHERE chair_id=%s", (iid,)) \
             and db_manager.execute("DELETE FROM instructor WHERE instructor_id=%s", (iid,))

        return redirect('/instructors') if ok else "<h2>Delete failed.</h2>"

    return render_template("instructors/delete_instructor.html")

@app.route('/courses')
def courses():
    sort = request.args.get('sort', 'course_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')

    base = """
        SELECT c.course_id, c.course_code, c.course_name, c.credits, d.department_name
        FROM course c
        LEFT JOIN department d ON c.department_id = d.department_id
        WHERE c.course_name LIKE %s OR c.course_code LIKE %s
    """

    data = db_manager.query_dict(base + f" ORDER BY {sort} {order}",
                                 (f"%{search}%", f"%{search}%"))

    return render_template("courses/courses.html",
                           courses=data, sort=sort, order=order, search=search)


@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        dept = request.form['department_id']
        code = request.form['course_code']
        name = request.form['course_name']
        credits = request.form['credits']

        ok = db_manager.execute("""
            INSERT INTO course (department_id, course_code, course_name, credits)
            VALUES (%s,%s,%s,%s)
        """, (dept, code, name, credits))

        return redirect('/courses') if ok else "<h2>Insert failed.</h2>"
    return render_template("courses/add_course.html")


@app.route('/delete_course', methods=['GET', 'POST'])
def delete_course():
    if request.method == 'POST':
        cid = request.form['course_id']

        # Delete enrollments for all sections of this course
        ok = db_manager.execute("""
            DELETE e FROM enrollment e
            JOIN section s ON e.section_id = s.section_id
            WHERE s.course_id=%s
        """, (cid,)) and db_manager.execute(
            "DELETE FROM section WHERE course_id=%s", (cid,)
        ) and db_manager.execute(
            "DELETE FROM course WHERE course_id=%s", (cid,)
        )

        return redirect('/courses') if ok else "<h2>Delete failed.</h2>"

    return render_template("courses/delete_course.html")


# -------------------------------
# DEPARTMENTS
# -------------------------------
@app.route('/departments')
def departments():
    sort = request.args.get('sort', 'department_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')

    data = db_manager.query_dict(f"""
        SELECT d.department_id, d.department_name, d.office_location,
               CONCAT(i.first_name,' ',i.last_name) AS chair_name
        FROM department d
        LEFT JOIN instructor i ON d.chair_id = i.instructor_id
        WHERE d.department_name LIKE %s OR d.office_location LIKE %s
        ORDER BY {sort} {order}
    """, (f"%{search}%", f"%{search}%"))

    return render_template("departments/departments.html",
                           departments=data, sort=sort, order=order, search=search)


@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        name = request.form['department_name']
        office = request.form['office_location']

        ok = db_manager.execute("""
            INSERT INTO department (department_name, office_location)
            VALUES (%s,%s)
        """, (name, office))

        return redirect('/departments') if ok else "<h2>Insert failed.</h2>"

    return render_template("departments/add_department.html")


@app.route('/delete_department', methods=['GET', 'POST'])
def delete_department():
    if request.method == 'POST':
        did = request.form['department_id']

        ok = db_manager.execute(
            "UPDATE instructor SET department_id=NULL WHERE department_id=%s", (did,)
        ) and db_manager.execute(
            "UPDATE course SET department_id=NULL WHERE department_id=%s", (did,)
        ) and db_manager.execute(
            "DELETE FROM department WHERE department_id=%s", (did,)
        )

        return redirect('/departments') if ok else "<h2>Delete failed.</h2>"

    return render_template("departments/delete_department.html")


@app.route('/sections')
def sections():
    sort = request.args.get('sort', 'section_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')

    data = db_manager.query_dict(f"""
        SELECT s.section_id, c.course_code, s.section_code, s.term, s.year,
               s.days, s.time, s.location,
               CONCAT(i.first_name,' ',i.last_name) AS instructor
        FROM section s
        JOIN course c ON s.course_id = c.course_id
        LEFT JOIN instructor i ON s.instructor_id = i.instructor_id
        WHERE s.section_code LIKE %s OR c.course_code LIKE %s
              OR CONCAT(i.first_name,' ',i.last_name) LIKE %s
        ORDER BY {sort} {order}
    """, (f"%{search}%", f"%{search}%", f"%{search}%"))

    return render_template("sections/sections.html",
                           sections=data, sort=sort, order=order, search=search)


@app.route('/add_section', methods=['GET', 'POST'])
def add_section():
    if request.method == 'POST':
        fields = (
            request.form['course_id'],
            request.form['instructor_id'],
            request.form['section_code'],
            request.form['term'],
            request.form['year'],
            request.form['days'],
            request.form['time'],
            request.form['capacity'],
            request.form['location']
        )

        ok = db_manager.execute("""
            INSERT INTO section (course_id, instructor_id, section_code,
                                 term, year, days, time, capacity, location)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, fields)

        return redirect('/sections') if ok else "<h2>Insert failed.</h2>"
    return render_template("sections/add_section.html")

@app.route('/delete_section', methods=['GET', 'POST'])
def delete_section():
    if request.method == 'POST':
        sid = request.form['section_id']

        ok = db_manager.execute(
            "DELETE FROM enrollment WHERE section_id=%s", (sid,)
        ) and db_manager.execute(
            "DELETE FROM section WHERE section_id=%s", (sid,)
        )

        return redirect('/sections') if ok else "<h2>Delete failed.</h2>"
    return render_template("sections/delete_section.html")


@app.route('/enrollments')
def enrollments():
    sort = request.args.get('sort', 'enrollment_id')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')

    data = db_manager.query_dict(f"""
        SELECT e.enrollment_id,
               CONCAT(s.first_name,' ',s.last_name) AS student_name,
               c.course_code, c.course_name, e.grade
        FROM enrollment e
        JOIN student s ON e.student_id = s.student_id
        JOIN section se ON e.section_id = se.section_id
        JOIN course c ON se.course_id = c.course_id
        WHERE CONCAT(s.first_name,' ',s.last_name) LIKE %s
           OR c.course_code LIKE %s OR c.course_name LIKE %s
        ORDER BY {sort} {order}
    """, (f"%{search}%", f"%{search}%", f"%{search}%"))

    return render_template("enrollments/enrollments.html",
                           enrollments=data, sort=sort, order=order, search=search)


@app.route('/add_enrollment', methods=['GET', 'POST'])
def add_enrollment():
    if request.method == 'POST':
        ok = db_manager.execute("""
            INSERT INTO enrollment (student_id, section_id, grade)
            VALUES (%s,%s,%s)
        """, (
            request.form['student_id'],
            request.form['section_id'],
            request.form['grade']
        ))

        return redirect('/enrollments') if ok else "<h2>Insert failed.</h2>"
    return render_template("enrollments/add_enrollment.html")

@app.route('/delete_enrollment', methods=['GET', 'POST'])
def delete_enrollment():
    if request.method == 'POST':
        eid = request.form['enrollment_id']
        ok = db_manager.execute("DELETE FROM enrollment WHERE enrollment_id=%s", (eid,))
        return redirect('/enrollments') if ok else "<h2>Delete failed.</h2>"
    return render_template("enrollments/delete_enrollment.html")

@app.route('/reports', methods=['GET', 'POST'])
def reports():
    busiest = complex.get_highest_enrolled_sections()
    dept_stats = complex.get_department_stats()
    majors = []
    transcripts = []
    selected_major = None
    selected_student = None

    if request.method == "POST":
        selected_major = request.form.get("major")
        selected_student = request.form.get("student_id")

        if selected_major:
            majors = complex.get_students_by_major(selected_major)

        if selected_student:
            transcripts = complex.student_transcript(selected_student)

    top_gpa = complex.get_top_students_by_gpa()

    return render_template("reports/reports.html",
        busiest_sections=busiest,
        department_stats=dept_stats,
        student_major=majors,
        selected_major=selected_major,
        top_gpa_students=top_gpa,
        student_transcripts=transcripts,
        selected_student_id=selected_student)

@app.route("/generate-data", methods=["POST"])
def generate_data():
    generate_data_main()  # call generate_data.py
    flash("Database has been reset and populated successfully!")
    return redirect(url_for("home"))  # redirect to main page

@app.route('/')
def home():
    return render_template("index.html")
if __name__ == '__main__':
    print("Flask server starting...")
    app.run(debug=True)