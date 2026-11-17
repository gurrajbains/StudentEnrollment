
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

# Share SQLAlchemy, bcrypt, and JWT extensions across backend modules.
database: SQLAlchemy
bcrypt: Bcrypt
jwt: JWTManager


# Attach SQLAlchemy to Flask for database operations.
def init_database(app: Flask) -> SQLAlchemy:
    global database
    database = SQLAlchemy(app)
    return database


# Initialize password hashing and verification.
def init_bcrypt(app: Flask):
    global bcrypt
    bcrypt = Bcrypt(app)
    return bcrypt


# Initialize JWT authentication for protected routes.
def init_jwt(app: Flask):
    global jwt
    jwt = JWTManager(app)
    return jwt
