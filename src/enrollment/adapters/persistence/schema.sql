CREATE TABLE IF NOT EXISTS programmes(programme_id TEXT NOT NULL PRIMARY KEY CHECK(typeof(programme_id)='text' AND length(programme_id)>0));
CREATE TABLE IF NOT EXISTS students(student_id TEXT NOT NULL PRIMARY KEY CHECK(typeof(student_id)='text' AND length(student_id)>0),programme_id TEXT NOT NULL CHECK(typeof(programme_id)='text' AND length(programme_id)>0),name TEXT NOT NULL CHECK(typeof(name)='text' AND required_text(name)),email TEXT NOT NULL CHECK(typeof(email)='text' AND required_text(email)));
CREATE TABLE IF NOT EXISTS courses(course_id TEXT NOT NULL PRIMARY KEY CHECK(typeof(course_id)='text' AND length(course_id)>0));
CREATE TABLE IF NOT EXISTS programme_course_offerings(programme_id TEXT NOT NULL REFERENCES programmes(programme_id) CHECK(typeof(programme_id)='text' AND length(programme_id)>0),course_id TEXT NOT NULL REFERENCES courses(course_id) CHECK(typeof(course_id)='text' AND length(course_id)>0),PRIMARY KEY(programme_id,course_id));
CREATE TABLE IF NOT EXISTS enrollments(student_id TEXT NOT NULL REFERENCES students(student_id) CHECK(typeof(student_id)='text' AND length(student_id)>0),course_id TEXT NOT NULL REFERENCES courses(course_id) CHECK(typeof(course_id)='text' AND length(course_id)>0),PRIMARY KEY(student_id,course_id));

CREATE UNIQUE INDEX IF NOT EXISTS students_email_key ON students(email_key(email));
