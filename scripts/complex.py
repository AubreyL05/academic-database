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
    print("--- Top 10 Heavily Enrolled Sections ---")
    results = db_manager.fetch_all(query)
    if results:
        # Print column headers manually for clarity
        print(f"{'Course Code':<15}{'Course Name':<30}{'Section Code':<15}{'Enrollments':<10}")
        print("-" * 70)
        for row in results:
            print(f"{row[0]:<15}{row[1]:<30}{row[2]:<15}{row[3]:<10}")
    else:
        print("No enrollment data found.")
        
    results = db_manager.fetch_all(query)
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
    print("\n--- Department Summary Statistics ---")
    results = db_manager.fetch_all(query)
    if results:
        print(f"{'Department Name':<35}{'Instructors':<15}{'Courses':<10}")
        print("-" * 60)
        for row in results:
            print(f"{row[0]:<35}{row[1]:<15}{row[2]:<10}")
    else:
        print("No department data found.")
        
    results = db_manager.fetch_all(query)
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
    print(f"\n--- Students Enrolled in {major_name} ---")
    results = db_manager.fetch_all(query, (major_name,))
    if results:
        print(f"{'First Name':<15}{'Last Name':<15}{'Email':<40}")
        print("-" * 70)
        for row in results:
            print(f"{row[0]:<15}{row[1]:<15}{row[2]:<40}")
    else:
        print(f"No students found for major: {major_name}")
        
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
    results = db_manager.fetch_all(query, (limit,))
    
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