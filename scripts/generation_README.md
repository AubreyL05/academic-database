# Breakdown of `generate_data.py`

## Headers and SQL connection
```python
import os
from dotenv import load_dotenv
from faker import Faker
import mysql.connector
import random

fake = Faker()
load_dotenv()

# Access database credentials
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

# Connect to MySQL database
db = mysql.connector.connect(
    host = db_host,
    user = db_user,
    password = db_password,
    database = db_name
)
cursor = db.cursor()
```
### Imports
* **dotenv** allows for the use of using an external file `.env` to hide confidential information such as sql database password. *Good Practice*
* **Faker** which is a Python library that allows the use of randomized fake names, numbers, dates, etc. Allows for making larger amounts of data easier.
*  **mysql.connector** allows for connection to the SQL database, so we can actually import the data into the tables.
* **random** allows for random assignments of attributes like majors.

### Database connection
* The function `mysql.connector.connect()` is used, which requires the `host`, `user`, `password`, & `database name`. This can be found in the email sent by Nathan Russell. This is what makes the connection to the correct database.
* `cursor`, which you will see a lot, is a function from the `mysql.connector` library. It is what allows us to interact with the database.
* `cursor = db.cursor()` essentially opens the cursor object so we can actually start inserting into the database.

### Common cursor methods
| Method | What it does |
|--------|--------------|
| `cursor.execute(sql, params)` | Executes a single SQL query. `params` are optional and help prevent SQL injection. |
| `cursor.executemany(sql, param_list)` | Executes the same query multiple times with a list of parameter tuples. |
| `cursor.fetchall()` | Fetches all rows from the last executed SELECT query. |
| `cursor.fetchone()` | Fetches one row at a time. |
| `cursor.close()` | Closes the cursor (clean up resources). |

## Departments
```python
department_courses = { # 10 classes for each department are listed here
}
departments = [
    # Listed 5 engineering departments and their office_location
]
cursor.executemany(
    "INSERT INTO department (department_name, office_location) VALUES (%s, %s)",
    departments
)
db.commit()
```
* `cursor.executemany()` This will prepare the departments = [] for appending the data into the database.
* Uses a sql command `INSERT INTO department` to find the correct table.
* in the argument for the INSERT - `(department_name, office_location) VALUES (%s, %s)` This what tells the cursor what data goes where so the first string will be `department_name` and the second string is `office_location`.
* `db.commit()` appends the data to the table.

## Instructors
```python
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
```
* `for dept_id in range(1, len(departments)+1):` Loops through each department so I can assign instructors to certain departments.
* `for i in range(10):` Decided to create 10 instructors for each department.
* `fake.*attribute*()` Will use the **Faker** library to create a fake name, number, or date to assign to the variable.
* `instructors.append()` appends all variables made to the instructors[] to execute.

```python
# Get instructor IDs to assign chairs
cursor.execute("SELECT instructor_id, department_id FROM instructor")
instructor_rows = cursor.fetchall()

# Assign the first instructor of each department as chair
for dept_id in range(1, len(departments)+1):
    chair = next((i[0] for i in instructor_rows if i[1] == dept_id), None)
    if chair:
        cursor.execute("UPDATE department SET chair_id = %s WHERE department_id = %s", (chair, dept_id))
db.commit()
```
* To assign one instructor as a chair for a department, I used just the first instructor using their id.
* Used `cursor.execute` to retrieve the instructor_id.
* `instructor_rows = cursor.fetchall()` Just collects the entire result of the query. `(instructor_id, department_id)`
* The second half just iterates through the departments again and uses the next() python function to assign the department chair to the first instructor found in each department.

## Students
```python
student_majors = [d[0] for d in departments]

students = []
for i in range(1250):
    first = fake.first_name()
    last = fake.last_name()
    email = f"{first.lower()}.{last.lower()}{i}@louisville.com"  # unique
    major = random.choice(student_majors)
    dob = fake.date_of_birth(minimum_age=18, maximum_age=25)
    students.append((first, last, email, major, dob))

cursor.executemany(
    "INSERT INTO student (first_name, last_name, email, major, date_of_birth) VALUES (%s,%s,%s,%s,%s)",
    students
)
db.commit()
```
* `student_majors = [d[0] for d in departments]` Assign student_majors to the first element in the department tuple, which would be the department name, [**Bioengineering**, 419 Paul C.Lutz Hall]
* Chose to do 1250 students, attributes assigned to each student similar to instructors. Using random.choice on the major so each student will be randomly assigned to a valid major.

## Courses
```python
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
```
* Not much different from other tables.
* Chose to just set the course code to be the first two letters of the major:
    * CSE = CO
    * CHE = CH

## Sections
```python
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
        time = f"{random.randint(8,16)}:00-{random.randint(9,17)}:30"
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
```
* Nothing too different from the other tables as well, just more filtering because you need to assign instructors and ensure all sections are in the same department.
* Chose to do 2 sections per course, **One small problem is just that this will make it where you will have one course have two sections in different terms, which isn't right.** I just ignored it for now.

## Enrollments
```python
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
```
* Also, not much different, just retrieved `student_id` and `section_id` so I could assign grades to each student in each section.

## IMPORTANT NOTES
### Be sure to close the cursor and close the DB.
```python
cursor.close()
db.close()
```
### Example `.env` file
```markdown
DB_HOST = cse335.courses.cse.louisville.edu
DB_USER = student_laaubr04
DB_PASSWORD = 9vic8d648l
DB_NAME = student_db_laaubr04
```