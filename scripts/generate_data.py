from faker import Faker
import random
import db_manager

def main():
    fake = Faker()

    print("Ensuring tables are initialized...")
    db_manager.reset_tables()
    print("Tables are ready.")

    db = db_manager.get_db()
    if db is None:
        print("Error: Could not connect to the database. Exiting.")
        exit(1)

    cursor = db.cursor()

    # ------------------- Departments -------------------
    department_courses = {
        'Bioengineering': ['Intro to Bioengineering', 'Biomaterials', 'Cell Engineering', 'Biomedical Imaging', 'Tissue Engineering', 'Biomechanics', 'Synthetic Biology', 'Bioinformatics', 'Biomedical Devices', 'Regenerative Medicine'],
        'Computer Science & Engineering': ['Intro to Programming', 'Data Structures', 'Algorithms', 'Computer Architecture', 'Operating Systems', 'Databases', 'Networks', 'Software Engineering', 'AI & Machine Learning', 'Embedded Systems'],
        'Chemical Engineering': ['Intro to ChemE', 'Thermodynamics', 'Transport Phenomena', 'Chemical Reaction Engineering', 'Process Control', 'Materials Science', 'Biochemical Engineering', 'Polymer Engineering', 'Process Design', 'Safety Engineering'],
        'Electrical & Computer Engineering': ['Circuit Analysis', 'Electronics', 'Signals & Systems', 'Digital Logic', 'Microprocessors', 'Communication Systems', 'Power Systems', 'Control Systems', 'Embedded Systems', 'VLSI Design'],
        'Mechanical Engineering': ['Statics', 'Dynamics', 'Mechanics of Materials', 'Thermodynamics', 'Fluid Mechanics', 'Heat Transfer', 'Mechanical Design', 'Robotics', 'Manufacturing Processes', 'Mechanical Vibrations']
    }

    departments = [
        ('Bioengineering', '419 Paul C.Lutz Hall'),
        ('Computer Science & Engineering', '222 Duthie Center'),
        ('Chemical Engineering', '106 Ernst Hall'),
        ('Electrical & Computer Engineering', '200 W.S. Speed Hall'),
        ('Mechanical Engineering', '110 Sackett Hall')
    ]

    cursor.executemany(
        "INSERT INTO department (department_name, office_location) VALUES (%s, %s)",
        departments
    )
    db.commit()

    # ------------------- Instructors -------------------
    instructors = []
    for dept_id in range(1, len(departments)+1):
        for i in range(10):
            first = fake.first_name()
            last = fake.last_name()
            email = f"{first.lower()}.{last.lower()}{dept_id}@louisville.com"  # unique
            instructors.append((first, last, email, dept_id))
    cursor.executemany(
        "INSERT INTO instructor (first_name, last_name, email, department_id) VALUES (%s,%s,%s,%s)",
        instructors
        )
    db.commit()

    # Get instructor IDs to assign chairs
    cursor.execute("SELECT instructor_id, department_id FROM instructor")
    instructor_rows = cursor.fetchall()

    # Assign the first instructor of each department as chair
    for dept_id in range(1, len(departments)+1):
        chair = next((i[0] for i in instructor_rows if i[1] == dept_id), None)
        if chair:
            cursor.execute("UPDATE department SET chair_id = %s WHERE department_id = %s", (chair, dept_id))
    db.commit()

    # ------------------- Students -------------------
    student_majors = [d[0] for d in departments]

    students = []
    for i in range(1250):
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}.{last.lower()}{i + 1}@louisville.com"  # unique
        major = random.choice(student_majors)
        dob = fake.date_of_birth(minimum_age=18, maximum_age=25)
        students.append((first, last, email, major, dob))

    cursor.executemany(
        "INSERT INTO student (first_name, last_name, email, major, date_of_birth) VALUES (%s,%s,%s,%s,%s)",
        students
    )
    db.commit()

    # ------------------- Courses -------------------
    courses = []
    course_id = 1
    for dept_id in range(1, len(departments)+1):
        for i in range(10):  # 10 courses per department
            dept_name = departments[dept_id-1][0]
            course_name = department_courses[dept_name][i]
            course_code = f"{dept_name[:2].upper()}{100+i+1}"  # CO101, ME102, etc.

            credits = random.choice([3, 4])
            courses.append((dept_id, course_name, course_code, credits))
            course_id += 1

    cursor.executemany(
        "INSERT INTO course (department_id, course_name, course_code, credits) VALUES (%s,%s,%s,%s)",
        courses
    )
    db.commit()

    # ------------------- Sections -------------------
    # Get instructor IDs again
    cursor.execute("SELECT instructor_id, department_id FROM instructor")
    instructor_rows = cursor.fetchall()

    sections = []
    section_id = 1
    terms = ['Fall', 'Spring']
    days_options = ['Mon/Wed/Fri', 'Tue/Thu']
    for course_id in range(1, len(courses)+1):
        # 2 sections per course
        for sec_num in range(2):
            # assign instructor from same department
            dept_id = courses[course_id-1][0]
            instructors_in_dept = [i[0] for i in instructor_rows if i[1]==dept_id]
            instructor_id = random.choice(instructors_in_dept)
            section_code = f"{courses[course_id-1][2]}-{sec_num+1:02d}"
            term = random.choice(terms)
            year = 2025
            startTime = random.randint(8, 16)
            time = f"{startTime:02d}:00-{random.randint(startTime, startTime + 1):02d}:30"
            days = random.choice(days_options)
            capacity = random.choice([25,30,35])
            location = f"{random.randint(100,500)} {fake.word().capitalize()} Hall"
            sections.append((course_id, instructor_id, section_code, term, year, time, days, capacity, location))
            section_id += 1

    cursor.executemany(
        "INSERT INTO section (course_id, instructor_id, section_code, term, year, time, days, capacity, location) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        sections
    )
    db.commit()

    # ------------------- Enrollments -------------------
    # Get student and section IDs
    cursor.execute("SELECT student_id FROM student")
    student_ids = [s[0] for s in cursor.fetchall()]
    cursor.execute("SELECT section_id FROM section")
    section_ids = [s[0] for s in cursor.fetchall()]

    enrollments = []
    grades = ['A','A-','B+','B','B-','C+','C','C-','D','F', None]

    for student_id in student_ids:
        # Each student enrolls in 4–6 random sections
        selected_sections = random.sample(section_ids, random.randint(4,6))
        for section_id in selected_sections:
            grade = random.choice(grades)
            enrollments.append((student_id, section_id, grade))

    cursor.executemany(
        "INSERT INTO enrollment (student_id, section_id, grade) VALUES (%s,%s,%s)",
        enrollments
    )
    db.commit()

    cursor.close()
    db.close()

    print("Database fully populated.")

if __name__ == "__main__":
    main()