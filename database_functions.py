from typing import Literal

import extensions
from database_models import Course, Enrollment, User


def createUser(
    username: str, 
    name: str, 
    password: str, 
    role: Literal["student", "teacher", "admin"]
) -> User:
    
    hashed_password = extensions.bcrypt.generate_password_hash(password).decode('utf-8')
    
    user = User(
        username=username, # type: ignore
        name=name, # type: ignore
        password=hashed_password, # type: ignore 
        role=role # type: ignore
    )

    return user

def createCourse(
    name: str,
    teacherID: int,
    time: str,
    capacity: int
) -> Course:
    course = Course(
        name=name, # type: ignore
        teacherID=teacherID, # type: ignore
        time=time, # type: ignore
        capacity=capacity # type: ignore
    )

    return course

def createEnrollment(
    student: User,
    course: Course,
    grade: str
) -> Enrollment:
    enrollment = Enrollment(
        student=student, # type: ignore
        course=course, # type: ignore
        grade=grade # type: ignore
    )

    return enrollment

def exampleDataExists() -> bool:
    return User.query.first() is not None

# Seed the database with example data from lab 8, including users, courses, and enrollments
def initExampleData():
    admin = createUser(
        username="admin", 
        name="System Admin", 
        password="password123", 
        role="admin"
    )

    teachers: dict[str, User] = {
        "Ralph Jenkins": createUser(
            username="rjenkins", 
            name="Ralph Jenkins", 
            password="password123", 
            role="teacher"
        ),
        "Susan Walker": createUser(
            username="swalker", 
            name="Susan Walker", 
            password="password123", 
            role="teacher"
        ),
        "Ammon Hepworth": createUser(
            username="ahepworth", 
            name="Ammon Hepworth", 
            password="password123", 
            role="teacher"
        )
    }

    students: dict[str, User] = {
        "Jose Santos": createUser(
            username="jsantos", 
            name="Jose Santos", 
            password="password123", 
            role="student"
        ),
        "Betty Brown": createUser(
            username="bbrown", 
            name="Betty Brown", 
            password="password123", 
            role="student"
        ),
        "John Stuart": createUser(
            username="jstuart", 
            name="John Stuart", 
            password="password123", 
            role="student"
        ),
        "Li Cheng": createUser(
            username="lcheng", 
            name="Li Cheng", 
            password="password123", 
            role="student"
        ),
        "Nancy Little": createUser(
            username="nlittle", 
            name="Nancy Little", 
            password="password123", 
            role="student"
        ),
        "Mindy Norris": createUser(
            username="mnorris", 
            name="Mindy Norris", 
            password="password123", 
            role="student"
        ),
        "Aditya Ranganath": createUser(
            username="aranganath", 
            name="Aditya Ranganath", 
            password="password123", 
            role="student"
        ),
        "Yi Wen chen": createUser(
            username="ychen", 
            name="Yi Wen chen", 
            password="password123", 
            role="student"
        ),
        "Chuck Norris": createUser(
            username="cnorris", 
            name="Chuck Norris", 
            password="password123", 
            role="student"
        )
    }

    all_users = [admin] + list(teachers.values()) + list(students.values())
    extensions.database.session.add_all(all_users)
    extensions.database.session.commit()  # Commit users to the database before creating courses

    courses: dict[str, Course] = {
        "Math 101": createCourse(
            name="Math 101",
            teacherID=teachers["Ralph Jenkins"].id,
            time="MWF 10:00-10:50 AM",
            capacity=8
        ),
        "Physics 121": createCourse(
            name="Physics 121",
            teacherID=teachers["Susan Walker"].id,
            time="TR 11:00-11:50 AM",
            capacity=10
        ),
        "CS 106": createCourse(
            name="CS 106",
            teacherID=teachers["Ammon Hepworth"].id,
            time="MWF 2:00-2:50 PM",
            capacity=10
        ),
        "CS 162": createCourse(
            name="CS 162",
            teacherID=teachers["Ralph Jenkins"].id,
            time="TR 3:00-3:50 PM",
            capacity=4
        )
    }

    extensions.database.session.add_all(courses.values())
    extensions.database.session.commit() # Commit courses to the database before creating enrollments

    enrollments: list[Enrollment] = [
        createEnrollment(
            student = students["Jose Santos"], 
            course = courses["Math 101"], 
            grade = "92"
        ),
        createEnrollment(
            student = students["Betty Brown"], 
            course = courses["Math 101"], 
            grade = "65"
        ),
        createEnrollment(
            student = students["John Stuart"], 
            course = courses["Math 101"], 
            grade = "86"
        ),
        createEnrollment(
            student = students["Li Cheng"], 
            course = courses["Math 101"], 
            grade = "77"
        ),

        createEnrollment(
            student = students["Nancy Little"], 
            course = courses["Physics 121"], 
            grade = "53"
        ),
        createEnrollment(
            student = students["Li Cheng"], 
            course = courses["Physics 121"], 
            grade = "85"
        ),
        createEnrollment(
            student = students["Mindy Norris"], 
            course = courses["Physics 121"], 
            grade = "94"
        ),
        createEnrollment(
            student = students["John Stuart"], 
            course = courses["Physics 121"], 
            grade = "91"
        ),
        createEnrollment(
            student = students["Betty Brown"], 
            course = courses["Physics 121"], 
            grade = "88"
        ),

        createEnrollment(
            student = students["Aditya Ranganath"], 
            course = courses["CS 106"], 
            grade = "93"
        ),
        createEnrollment(
            student = students["Yi Wen chen"], 
            course = courses["CS 106"], 
            grade = "85"
        ),
        createEnrollment(
            student = students["Nancy Little"], 
            course = courses["CS 106"], 
            grade = "57"
        ),
        createEnrollment(
            student = students["Mindy Norris"], 
            course = courses["CS 106"], 
            grade = "68"
        ),

        createEnrollment(
            student = students["Aditya Ranganath"], 
            course = courses["CS 162"], 
            grade = "99"
        ),
        createEnrollment(
            student = students["Yi Wen chen"], 
            course = courses["CS 162"], 
            grade = "92"
        ),
        createEnrollment(
            student = students["Nancy Little"], 
            course = courses["CS 162"], 
            grade = "87"
        ),
        createEnrollment(
            student = students["John Stuart"], 
            course = courses["CS 162"], 
            grade = "67"
        )
    ]
    extensions.database.session.add_all(enrollments)
    extensions.database.session.commit()  # Commit enrollments to the database