
from extensions import database


# Store student, teacher, and admin accounts with different roles.
class User(database.Model):
    id = database.Column(
        database.Integer, primary_key=True
    )
    username = database.Column(
        database.String(80), unique=True, nullable=False
    )
    name = database.Column(
        database.String(120), nullable=False
    )
    password = database.Column(
        database.String(255), nullable=False
    )  # BCrypt password hash
    role = database.Column(
        database.String(20), nullable=False
    )  # student, teacher, or admin

    def __repr__(self):
        return f"<User {self.username}>"

    # Convert a user record to JSON-safe data without the password.
    def toDict(self):
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "role": self.role
        }


# Store each course, its teacher, meeting time, and seat capacity.
class Course(database.Model):
    id = database.Column(
        database.Integer, primary_key=True
    )
    name = database.Column(
        database.String(80), nullable=False, unique=True
    )
    teacherID = database.Column(
        database.Integer,
        database.ForeignKey('user.id'),
        nullable=False
    )
    time = database.Column(
        database.String(80), nullable=False
    )
    capacity = database.Column(
        database.Integer, nullable=False
    )

    # Connect each course to its assigned teacher.
    teacher = database.relationship(
        "User",
        backref=database.backref("courses", lazy=True)
    )

    def __repr__(self):
        return f"<Course {self.name}>"

    # Include the current enrollment count in course API responses.
    def toDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "teacherID": self.teacherID,
            "teacher": self.teacher.name if self.teacher else "",
            "time": self.time,
            "capacity": self.capacity,
            "enrolled_count": len(self.enrollments) # type: ignore
        }


# Connect students to courses and store their grades.
class Enrollment(database.Model):
    id = database.Column(
        database.Integer, primary_key=True
    )
    studentID = database.Column(
        database.Integer,
        database.ForeignKey('user.id'),
        nullable=False
    )
    courseID = database.Column(
        database.Integer,
        database.ForeignKey('course.id'),
        nullable=False
    )
    grade = database.Column(
        database.String(10), nullable=True
    )  # Grade can remain empty until assigned.

    # Link enrollment records to their student and course.
    student = database.relationship(
        "User",
        backref=database.backref("enrollments", lazy=True)
    )
    course = database.relationship(
        "Course",
        backref=database.backref("enrollments", lazy=True)
    )

    def __repr__(self):
        return f"<Enrollment StudentID: {self.studentID}, CourseID: {self.courseID}, Grade: {self.grade}>"

    # Return enrollment data and related names for the admin interface.
    def toDict(self):
        return {
            "id": self.id,
            "studentID": self.studentID,
            "courseID": self.courseID,
            "grade": self.grade,
            "studentName": self.student.name if self.student else "",
            "courseName": self.course.name if self.course else ""
        }
