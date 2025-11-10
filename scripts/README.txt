This project is a full-stack Academic Database Management System built with Flask (Python), MySQL, and HTML/CSS.
It allows users to:

	- View, sort, and search data across Students, Instructors, Courses, Departments, Sections, and Enrollments

	- Add or delete records directly from the web interface

	- Use ascending/descending sorting toggles and a “Clear Filters” system

Everything runs locally using Flask and a MySQL instance on localhost.

-= Installation Requirements =-
	(1) Make sure Python 3.10+ is installed
	(2) Install flask with: " pip install flask mysql-connector-python " in a command prompt
	(3) Install MySQL.connector for python (I used VS Code for all of this)
	(4) Using either your own local instance or the CSE 335 server provided, run the create_table.sql query, then generate data using generate_data.py (make sure you specify your login!)

		--> Run this in order to create the necessary tables:
				CREATE DATABASE student; (make sure it's named student! if it is named something else, you must change the database in generate_data.py AND app.py)
				USE student;
					(Run your create_table.sql here to create all the required tables)
	
	(5) Now that your data is populated, input your database login once again in app.py
	(6) Once DB login is specified in app.py, right click inside of the CSE 335 project folder and click "Open in terminal." After that, type "python app.py" and the server will start.
	(7) Once server is started, you should be able to go to http://localhost:5000/ and see the Academic Database if everything works properly. If not, you probably don't have the right server connections.
		--> Make sure the server is started and on TCP 3306 (port 3306 in MySQL, which it should be)
Success!
