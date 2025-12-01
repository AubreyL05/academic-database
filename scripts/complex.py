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
        COUNT(DISTINCT c.course_id) AS num_courses,
        COUNT(DISTINCT sec.section_id) AS num_sections,
        COUNT(DISTINCT s.student_id) AS num_students
    FROM department d
    LEFT JOIN instructor i ON d.department_id = i.department_id
    LEFT JOIN course c ON d.department_id = c.department_id
    LEFT JOIN section sec ON c.course_id = sec.course_id
    LEFT JOIN student s ON s.major = d.department_name
    GROUP BY d.department_name
    ORDER BY num_instructors DESC;
    """
        
    results = db_manager.query_all(query)
    departments = []
    if results:
        for row in results:
            departments.append({
                "department_name": row[0],
                "num_instructors": row[1],
                "num_courses": row[2],
                "num_sections": row[3],
                "num_students": row[4]
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