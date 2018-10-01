import os

from flask import Flask, session, jsonify, redirect, request, render_template
from flask_session import Session
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

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


@app.route("/register", methods=["GET", "POST"])
def register():
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return "must provide username", 403

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "must provide password", 403

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if rows.rowcount != 1 or not check_password_hash(
                rows[0]["password_hash"], request.form.get("password")):
            return "invalid username and/or password", 403

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # TODO Redirect user to previous page
    return redirect("/")


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


def errorhandler(error):
    return render_template("error_render.html", error=error), error.code


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
