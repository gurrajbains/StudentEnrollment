from extensions import database


class User(database.Model):
    # Stores students, teachers, and admins in the same table with a role field to differentiate them
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
    )  # BCrypt hash (legacy column name)
    role = database.Column(
        database.String(20), nullable=False
    )  # 'student', 'admin'. or 'teacher'

    def __repr__(self):
        # Return a string representation of the user object
        return f"<User {self.username}>"
    
    def toDict(self):
        # Return a dictionary representation of the user object
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "role": self.role
        }


class Course(database.Model):
    # Stores the courses offered by the school, uses many-to-one relationship with user
    id = database.Column(
        database.Integer, primary_key=True
    )
    name = database.Column(
        database.String(80), nullable=False, unique=True
    )
    teacherID = database.Column(
        database.Integer, database.ForeignKey('user.id'), nullable=False
    )
    time = database.Column(database.String(80), nullable=False)
    capacity = database.Column(database.Integer, nullable=False)

    teacher = database.relationship("User", backref=database.backref("courses", lazy=True))

    def __repr__(self):
        return f"<Course {self.name}>"
    
    def toDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "teacherID": self.teacherID,
            "teacher": self.teacher.name if self.teacher else "",
            "time": self.time,
            "capacity": self.capacity,
            "enrolled_count": len(self.enrollments) # type: ignore
            # relationship is lazy-loaded, so we can use len() to get the count of enrollments
        }

class Enrollment(database.Model):
    # Junction table that connects students and courses, uses many-to-many relationship with grade field to store the grade of the student in the course
    id = database.Column(
        database.Integer, primary_key=True
    )
    studentID = database.Column(
        database.Integer, database.ForeignKey('user.id'), nullable=False
    )
    courseID = database.Column(
        database.Integer, database.ForeignKey('course.id'), nullable=False
    )
    grade = database.Column(
        database.String(10), nullable=True
    )  # Grade can be null if the student has not completed the course yet

    student= database.relationship(
        "User", backref=database.backref("enrollments", lazy=True)
    )
    course = database.relationship(
        "Course", backref=database.backref("enrollments", lazy=True)
    )

    def __repr__(self):
        return f"<Enrollment StudentID: {self.studentID}, CourseID: {self.courseID}, Grade: {self.grade}>"

    def toDict(self):
        return {
            "id": self.id,
            "studentID": self.studentID,
            "courseID": self.courseID,
            "grade": self.grade,
            "studentName": self.student.name if self.student else "",
            "courseName": self.course.name if self.course else ""
        }