CREATE TABLE IF NOT EXISTS programmes(programme_id TEXT NOT NULL PRIMARY KEY CHECK(typeof(programme_id)='text' AND length(programme_id)>0));
CREATE TABLE IF NOT EXISTS students(student_id TEXT NOT NULL PRIMARY KEY CHECK(typeof(student_id)='text' AND length(student_id)>0),programme_id TEXT NOT NULL CHECK(typeof(programme_id)='text' AND length(programme_id)>0),name TEXT NOT NULL CHECK(typeof(name)='text' AND required_text(name)),email TEXT NOT NULL CHECK(typeof(email)='text' AND required_text(email)),saved_version INTEGER NOT NULL CHECK(typeof(saved_version)='integer' AND saved_version>=1 AND saved_version<=9223372036854775807));
CREATE TABLE IF NOT EXISTS courses(course_id TEXT NOT NULL PRIMARY KEY CHECK(typeof(course_id)='text' AND length(course_id)>0));
CREATE TABLE IF NOT EXISTS programme_course_offerings(programme_id TEXT NOT NULL REFERENCES programmes(programme_id) CHECK(typeof(programme_id)='text' AND length(programme_id)>0),course_id TEXT NOT NULL REFERENCES courses(course_id) CHECK(typeof(course_id)='text' AND length(course_id)>0),PRIMARY KEY(programme_id,course_id));
CREATE TABLE IF NOT EXISTS enrollments(student_id TEXT NOT NULL REFERENCES students(student_id) CHECK(typeof(student_id)='text' AND length(student_id)>0),course_id TEXT NOT NULL REFERENCES courses(course_id) CHECK(typeof(course_id)='text' AND length(course_id)>0),PRIMARY KEY(student_id,course_id));

CREATE UNIQUE INDEX IF NOT EXISTS students_email_key ON students(email_key(email));

-- Student saved_version is NOT NULL INTEGER with strict SQLite typeof(...)=integer and positive signed-64 range.
-- A validation-only BEFORE UPDATE guard rejects any Student update whose new saved_version is not exactly the previous value plus one, including unchanged-detail writes.
CREATE TRIGGER IF NOT EXISTS students_saved_version_guard BEFORE UPDATE ON students
WHEN typeof(NEW.saved_version)!='integer' OR NEW.saved_version<1
 OR OLD.saved_version>=9223372036854775807 OR NEW.saved_version!=OLD.saved_version+1
BEGIN
 SELECT RAISE(ABORT,'invalid saved version advancement');
END;
