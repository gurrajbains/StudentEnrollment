import os
from functools import wraps
from pathlib import Path
from typing import Literal

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_jwt_extended import (create_access_token,
                                get_jwt_identity, jwt_required,
                                set_access_cookies, unset_jwt_cookies,
                                verify_jwt_in_request)
from sqlalchemy.exc import IntegrityError

import encryption
import extensions

app = Flask(
    __name__, 
    static_folder='static', 
    static_url_path='/static', 
    template_folder='templates'
)

INSTANCE_PATH = Path(app.instance_path)
INSTANCE_PATH.mkdir(parents=True, exist_ok=True)

FLASK_SECRET_FILE = encryption.init_secret_file(
    INSTANCE_PATH / "flask_secret.txt"
)
JWT_SECRET_FILE = encryption.init_secret_file(
    INSTANCE_PATH / "jwt_secret.txt"
)

# Database configurations
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///enrollment.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = (
    os.getenv("FLASK_SECRET_KEY") or 
    encryption.get_secret(FLASK_SECRET_FILE)
)
app.config["JWT_SECRET_KEY"] = (
    os.getenv("JWT_SECRET_KEY") or 
    encryption.get_secret(JWT_SECRET_FILE)
)
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = os.getenv("COOKIE_SECURE", "0") == "1"
app.config["JWT_COOKIE_CSRF_PROTECT"] = True

# initialize shared instances accross the app
extensions.init_database(app)
extensions.init_bcrypt(app)
extensions.init_jwt(app)

import database_functions
from database_models import Course, Enrollment, User


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

def get_page_for(role: Literal["student", "teacher", "admin"]) -> str:
    return {
        "student": "student.html", 
        "teacher": "teacher.html", 
        "admin": "admin.html"
    }[role]

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
    if not user or not extensions.bcrypt.check_password_hash(user.password, password):
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
    course = extensions.database.session.get(Course, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    if Enrollment.query.filter_by(studentID=user.id, courseID=course_id).first():
        return jsonify({"error": "Already enrolled"}), 409
    if len(course.enrollments) >= course.capacity:
        return jsonify({"error": "Class is full"}), 409
    extensions.database.session.add(Enrollment(studentID=user.id, courseID=course_id))
    extensions.database.session.commit()
    return jsonify({"message": "Enrolled", "course_id": course_id}), 201

@app.route("/api/student/courses/<int:course_id>", methods=["DELETE"])
@role_required("student")
def student_drop(course_id):
    enrollment = Enrollment.query.filter_by(studentID=current_user().id, courseID=course_id).first()
    if not enrollment:
        return jsonify({"error": "Enrollment not found"}), 404
    extensions.database.session.delete(enrollment)
    extensions.database.session.commit()
    return jsonify({"message": "Dropped"})

@app.route("/api/teacher/courses")
@role_required("teacher")
def teacher_courses():
    return jsonify([c.toDict() for c in Course.query.filter_by(teacherID=current_user().id).all()])

@app.route("/api/teacher/courses/<int:course_id>/students")
@role_required("teacher")
def teacher_roster(course_id):
    course = extensions.database.session.get(Course, course_id)
    if not course or course.teacherID != current_user().id:
        return jsonify({"error": "Class not found"}), 404
    return jsonify([{"id": e.studentID, "name": e.student.name, "grade": e.grade} for e in course.enrollments])

@app.route("/api/teacher/courses/<int:course_id>/students/<int:student_id>/grade", methods=["PATCH"])
@role_required("teacher")
def update_grade(course_id, student_id):
    course = extensions.database.session.get(Course, course_id)
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
    extensions.database.session.commit()
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
            data["password"] = extensions.bcrypt.generate_password_hash(data["password"]).decode("utf-8")
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
            teacher = extensions.database.session.get(User, data["teacherID"]) if type(data["teacherID"]) is int else None
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
        student = extensions.database.session.get(User, sid) if type(sid) is int else None
        course = extensions.database.session.get(Course, cid) if type(cid) is int else None
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
    record = extensions.database.session.get(model, record_id) if record_id is not None else None
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
        extensions.database.session.delete(record)
        extensions.database.session.commit()
        return jsonify({"message": "Deleted"})
    try:
        data = validate_record(resource, request.get_json(silent=True), record)
        if request.method == "POST":
            record = model(**data)
            extensions.database.session.add(record)
        else:
            for key, value in data.items():
                setattr(record, key, value)
        extensions.database.session.commit()
        return jsonify(serialize_record(resource, record)), 201 if request.method == "POST" else 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except IntegrityError:
        extensions.database.session.rollback()
        return jsonify({"error": "Duplicate or invalid database relation"}), 409

if __name__ == "__main__":
    with app.app_context():
        extensions.database.create_all()

        if not database_functions.exampleDataExists():
            database_functions.initExampleData()

    app.run(
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        port=int(os.getenv("PORT", "5000")),
    )