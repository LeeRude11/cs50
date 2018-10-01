import os

from flask import Flask, session, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return "Project 1: TODO"


@app.route("/registration", methods=["GET", "POST"])
def registration():
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    return None


@app.route("/logout")
def logout():
    return None


@app.route("/search", methods=["GET", "POST"])
def search():
    return None


# TODO render review option for authorised
@app.route("/book_page")
def book_page():
    # TODO call GoodReads; helpers?
    return None


# TODO redirect to login for unauthorised
@app.route("/review", methods=["GET", "POST"])
def review():
    return None


@app.route("/api/<isbn>")
def api():
    return jsonify(None)
