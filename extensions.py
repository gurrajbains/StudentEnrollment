from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

# Gets initialized in app.py
database: SQLAlchemy 
bcrypt: Bcrypt
jwt: JWTManager

def init_database(app: Flask) -> SQLAlchemy:
    global database
    database = SQLAlchemy(app)
    return database

def init_bcrypt(app: Flask):
    global bcrypt
    bcrypt = Bcrypt(app)
    return bcrypt

def init_jwt(app: Flask):
    global jwt
    jwt = JWTManager(app)
    return jwt