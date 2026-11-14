from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity, verify_jwt_in_request

import os
import secrets
from functools import wraps
from sqlalchemy.exc import IntegrityError

app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')

def local_secret(filename):
    """Per-install local secret: never commit it to GitHub."""
    os.makedirs(app.instance_path, exist_ok=True)
    path = os.path.join(app.instance_path, filename)
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as target:
            target.write(secrets.token_hex(32))
    with open(path, encoding='utf-8') as source:
        return source.read().strip()


# Database configurations
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///enrollment.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = os.getenv("FLASK_SECRET_KEY") or local_secret("flask_secret.txt")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY") or local_secret("jwt_secret.txt")
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = os.getenv("COOKIE_SECURE", "0") == "1"
app.config["JWT_COOKIE_CSRF_PROTECT"] = True

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Database Models
class User(db.Model):
    # Stores students, teachers, and admins in the same table with a role field to differentiate them
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(255), nullable=False)  # BCrypt hash (legacy column name)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'admin'. or 'teacher'

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
class Course(db.Model):
    # Stores the courses offered by the school, uses many-to-one relationship with user
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    teacherID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time = db.Column(db.String(80), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

    teacher = db.relationship("User", backref=db.backref("courses", lazy=True))

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
            "enrolled_count": len(self.enrollments)
        }

class Enrollment(db.Model):
    # Junction table that connects students and courses, uses many-to-many relationship with grade field to store the grade of the student in the course
    id = db.Column(db.Integer, primary_key=True)
    studentID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    courseID = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    grade = db.Column(db.String(10), nullable=True)

    student= db.relationship("User", backref=db.backref("enrollments", lazy=True))
    course = db.relationship("Course", backref=db.backref("enrollments", lazy=True))

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

# Database intialization with example Data Seeding
def createUser(username, name, password, role):
    #Hash password using lecture 16
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, name=name, password=hashed_password, role=role)
    db.session.add(user)
    return user

# Seed the database with example data from lab 8, including users, courses, and enrollments
def seedDatabase():
    db.create_all()
    if User.query.first() is not None:
        return # database already seeded

    #Creating users based on example data from Lab 8
    createUser("admin", "System Admin", "password123" , "admin") # Create an admin user
    rjenkins = createUser("rjenkins", "Ralph Jenkins", "password123" , "teacher") # Creating teacher users
    swalker = createUser("swalker", "Susan Walker" , "password123" , "teacher")
    ahepworth = createUser("ahepworth", "Ammon Hepworth", "password123" , "teacher")

    students = {
        "Jose Santos": createUser("jsantos", "Jose Santos", "password123" , "student"),
        "Betty Brown": createUser("bbrown", "Betty Brown", "password123" , "student"),
        "John Stuart": createUser("jstuart", "John Stuart", "password123" , "student"),
        "Li Cheng": createUser("lcheng", "Li Cheng", "password123" , "student"),
        "Nancy Little": createUser("nlittle", "Nancy Little", "password123" , "student"),
        "Mindy Norris": createUser("mnorris", "Mindy Norris", "password123" , "student"),
        "Aditya Ranganath": createUser("aranganath", "Aditya Ranganath", "password123" , "student"),
        "Yi Wen chen": createUser("ychen", "Yi Wen chen", "password123" , "student"),
        "Chuck Norris": createUser("cnorris", "Chuck Norris", "password123" , "student")
    }

    db.session.commit()  # Commit users to the database before creating courses

    math101 = Course(name="Math 101", teacherID=rjenkins.id, time="MWF 10:00-10:50 AM", capacity=8)
    phys121 = Course(name="Physics 121", teacherID=swalker.id, time="TR 11:00-11:50 AM", capacity=10)
    cs106 = Course(name="CS 106", teacherID=ahepworth.id, time="MWF 2:00-2:50 PM", capacity=10)
    cs162 = Course(name="CS 162", teacherID=ahepworth.id, time="TR 3:00-3:50 PM", capacity=4)

    db.session.add_all([math101, phys121, cs106, cs162])
    db.session.commit()  # Commit courses to the database before creating enrollments

    initialEnrollments = [
        (math101, "Jose Santos" , 92),
        (math101, "Betty Brown" , 65),
        (math101, "John Stuart" , 86),
        (math101, "Li Cheng" , 77),

        (phys121, "Nancy Little" , 53),
        (phys121, "Li Cheng" , 85),
        (phys121, "Mindy Norris" , 94),
        (phys121, "John Stuart" , 91),
        (phys121, "Betty Brown", 88),

        (cs106, "Aditya Ranganath" , 93),
        (cs106, "Yi Wen chen" , 85),
        (cs106, "Nancy Little" , 57),
        (cs106, "Mindy Norris" , 68),

        (cs162, "Aditya Ranganath" , 99),
        (cs162, "Yi Wen chen" , 92),
        (cs162, "Nancy Little" , 87),
        (cs162, "John Stuart" , 67)
    ]

    for course_obj, studentName, grade in initialEnrollments:
        enrollment = Enrollment(
            student = students[studentName],
            course = course_obj,
            grade = str(grade)  # Store grade as string

        )
        db.session.add(enrollment)

    db.session.commit()  # Commit enrollments to the database

# Role-restricted pages (the server enforces access, not just the navigation).
def role_required(role):
    def decorate(func):
        @wraps(func)
        @jwt_required()
        def wrapped(*args, **kwargs):
            current = current_user()
            if current is None or current.role != role:
                return jsonify({"error": "Forbidden"}), 403
            return func(*args, **kwargs)
        return wrapped
    return decorate

def current_user():
    username = get_jwt_identity()
    return User.query.filter_by(username=username).first()

def page_for(role):
    return {"student": "student.html", "teacher": "teacher.html", "admin": "admin.html"}.get(role)

@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")

@app.route("/<role>.html")
def dashboard(role):
    if role not in ("student", "teacher", "admin"):
        return jsonify({"error": "Not found"}), 404
    try:
        verify_jwt_in_request()
        user = current_user()
    except Exception:
        return redirect(url_for("index"))
    if not user or user.role != role:
        return jsonify({"error": "Forbidden"}), 403
    return render_template(role + ".html")

@app.route("/login", methods=["POST"])
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid username or password"}), 401
    response = jsonify({"message": "Login successful", "user": user.toDict()})
    set_access_cookies(response, create_access_token(identity=user.username))
    return response

@app.route("/logout", methods=["POST"])
@app.route("/api/logout", methods=["POST"])
@jwt_required()
def logout():
    response = jsonify({"message": "Logged out"})
    unset_jwt_cookies(response)
    return response

@app.route("/api/me")
@jwt_required()
def me():
    user = current_user()
    return jsonify(user.toDict()) if user else (jsonify({"error": "Unknown user"}), 404)

@app.route("/api/courses")
@role_required("student")
def course_catalog():
    return jsonify([c.toDict() for c in Course.query.order_by(Course.name).all()])

@app.route("/api/student/courses", methods=["GET", "POST"])
@role_required("student")
def student_courses():
    user = current_user()
    if request.method == "GET":
        return jsonify([e.course.toDict() for e in Enrollment.query.filter_by(studentID=user.id).all()])
    data = request.get_json(silent=True) or {}
    course_id = data.get("course_id")
    if type(course_id) is not int:
        return jsonify({"error": "course_id must be an integer"}), 400
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    if Enrollment.query.filter_by(studentID=user.id, courseID=course_id).first():
        return jsonify({"error": "Already enrolled"}), 409
    if len(course.enrollments) >= course.capacity:
        return jsonify({"error": "Class is full"}), 409
    db.session.add(Enrollment(studentID=user.id, courseID=course_id))
    db.session.commit()
    return jsonify({"message": "Enrolled", "course_id": course_id}), 201

@app.route("/api/student/courses/<int:course_id>", methods=["DELETE"])
@role_required("student")
def student_drop(course_id):
    enrollment = Enrollment.query.filter_by(studentID=current_user().id, courseID=course_id).first()
    if not enrollment:
        return jsonify({"error": "Enrollment not found"}), 404
    db.session.delete(enrollment)
    db.session.commit()
    return jsonify({"message": "Dropped"})

@app.route("/api/teacher/courses")
@role_required("teacher")
def teacher_courses():
    return jsonify([c.toDict() for c in Course.query.filter_by(teacherID=current_user().id).all()])

@app.route("/api/teacher/courses/<int:course_id>/students")
@role_required("teacher")
def teacher_roster(course_id):
    course = db.session.get(Course, course_id)
    if not course or course.teacherID != current_user().id:
        return jsonify({"error": "Class not found"}), 404
    return jsonify([{"id": e.studentID, "name": e.student.name, "grade": e.grade} for e in course.enrollments])

@app.route("/api/teacher/courses/<int:course_id>/students/<int:student_id>/grade", methods=["PATCH"])
@role_required("teacher")
def update_grade(course_id, student_id):
    course = db.session.get(Course, course_id)
    if not course or course.teacherID != current_user().id:
        return jsonify({"error": "Class not found"}), 404
    enrollment = Enrollment.query.filter_by(courseID=course_id, studentID=student_id).first()
    if not enrollment:
        return jsonify({"error": "Student not enrolled"}), 404
    data = request.get_json(silent=True) or {}
    grade = data.get("grade")
    if type(grade) not in (int, float) or not 0 <= grade <= 100:
        return jsonify({"error": "Grade must be a number from 0 to 100"}), 400
    enrollment.grade = str(grade)
    db.session.commit()
    return jsonify({"message": "Grade saved", "grade": enrollment.grade})

ALLOWED_RESOURCES = {"users": User, "courses": Course, "enrollments": Enrollment}

def serialize_record(resource, record):
    return record.toDict()

def validate_record(resource, data, existing=None):
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    if resource == "users":
        fields = {"username", "name", "role", "password"}
        if set(data) - fields:
            raise ValueError("Unknown user field")
        if "role" in data and data["role"] not in ("student", "teacher", "admin"):
            raise ValueError("Invalid role")
        if existing is None and not fields.issubset(data):
            raise ValueError("username, name, role, password required")
        for k in ("username", "name", "password"):
            if k in data and (not isinstance(data[k], str) or not data[k].strip()):
                raise ValueError(k + " must be a nonempty string")
        if "password" in data:
            data["password"] = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    elif resource == "courses":
        fields = {"name", "teacherID", "time", "capacity"}
        if set(data) - fields:
            raise ValueError("Unknown course field")
        if existing is None and not fields.issubset(data):
            raise ValueError("name, teacherID, time, capacity required")
        if "capacity" in data and (type(data["capacity"]) is not int or data["capacity"] < 1):
            raise ValueError("capacity must be a positive integer")
        if existing is not None and "capacity" in data and data["capacity"] < len(existing.enrollments):
            raise ValueError("capacity cannot be below current enrollment")
        if "teacherID" in data:
            teacher = db.session.get(User, data["teacherID"]) if type(data["teacherID"]) is int else None
            if not teacher or teacher.role != "teacher":
                raise ValueError("teacherID must identify a teacher")
        for k in ("name", "time"):
            if k in data and (not isinstance(data[k], str) or not data[k].strip()):
                raise ValueError(k + " must be a nonempty string")
    else:
        fields = {"studentID", "courseID", "grade"}
        if set(data) - fields:
            raise ValueError("Unknown enrollment field")
        if existing is None and not {"studentID", "courseID"}.issubset(data):
            raise ValueError("studentID and courseID required")
        sid = data.get("studentID", existing.studentID if existing else None)
        cid = data.get("courseID", existing.courseID if existing else None)
        student = db.session.get(User, sid) if type(sid) is int else None
        course = db.session.get(Course, cid) if type(cid) is int else None
        if not student or student.role != "student" or not course:
            raise ValueError("studentID must be a student and courseID must exist")
        other = Enrollment.query.filter_by(studentID=sid, courseID=cid).first()
        if other and (existing is None or other.id != existing.id):
            raise ValueError("Duplicate enrollment")
        if (existing is None or existing.courseID != cid) and len(course.enrollments) >= course.capacity:
            raise ValueError("Course is full")
        if "grade" in data and data["grade"] is not None:
            try:
                value = float(data["grade"])
            except (TypeError, ValueError):
                raise ValueError("Invalid grade")
            if not 0 <= value <= 100:
                raise ValueError("Grade must be between 0 and 100")
            data["grade"] = str(value)
    return data

@app.route("/api/admin/<resource>", methods=["GET", "POST"])
@app.route("/api/admin/<resource>/<int:record_id>", methods=["GET", "PUT", "DELETE"])
@role_required("admin")
def admin_records(resource, record_id=None):
    model = ALLOWED_RESOURCES.get(resource)
    if not model:
        return jsonify({"error": "Unknown resource"}), 404
    record = db.session.get(model, record_id) if record_id is not None else None
    if record_id is not None and record is None:
        return jsonify({"error": "Record not found"}), 404
    if request.method == "GET":
        return jsonify(serialize_record(resource, record)) if record else jsonify([serialize_record(resource, item) for item in model.query.all()])
    if request.method == "DELETE":
        if resource == "users" and record.id == current_user().id:
            return jsonify({"error": "Cannot delete own account"}), 400
        if resource == "users" and (record.enrollments or record.courses):
            return jsonify({"error": "User is referenced by classes or enrollments"}), 409
        if resource == "courses" and record.enrollments:
            return jsonify({"error": "Remove enrollments before deleting course"}), 409
        db.session.delete(record)
        db.session.commit()
        return jsonify({"message": "Deleted"})
    try:
        data = validate_record(resource, request.get_json(silent=True), record)
        if request.method == "POST":
            record = model(**data)
            db.session.add(record)
        else:
            for key, value in data.items():
                setattr(record, key, value)
        db.session.commit()
        return jsonify(serialize_record(resource, record)), 201 if request.method == "POST" else 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Duplicate or invalid database relation"}), 409

if __name__ == "__main__":
    with app.app_context():
        seedDatabase()
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1", port=int(os.getenv("PORT", "5000")))
