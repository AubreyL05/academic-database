USE student_db_laaubr04;

SELECT * FROM student;
-- SELECT * FROM department;
-- SELECT * FROM instructor;
SELECT * FROM course;
-- SELECT * FROM section;
-- SELECT * FROM enrollment LIMIT 5100;

-- List sections with their course name and instructor
SELECT sec.section_code, c.course_name, i.first_name AS instructor_first, i.last_name AS instructor_last, sec.term, sec.year
FROM section sec
JOIN course c ON sec.course_id = c.course_id
JOIN instructor i ON sec.instructor_id = i.instructor_id
ORDER BY sec.section_code;

SELECT s.student_id, s.first_name, s.last_name, s.email, s.major
FROM student s
JOIN enrollment e ON s.student_id = e.student_id
JOIN section sec ON e.section_id = sec.section_id
JOIN course c ON sec.course_id = c.course_id
WHERE c.course_name = 'Intro to Programming';

-- List student enrollments
-- SELECT s.first_name, s.last_name, sec.section_code, c.course_name, e.grade
-- FROM enrollment e
-- JOIN student s ON e.student_id = s.student_id
-- JOIN section sec ON e.section_id = sec.section_id
-- JOIN course c ON sec.course_id = c.course_id;