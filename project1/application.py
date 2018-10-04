import os

from flask import Flask, session, jsonify, redirect, request, render_template
from flask_session import Session
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
if not os.getenv("API_KEY"):
    raise RuntimeError("API_KEY is not set")


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# GoodReads API
API_KEY = os.getenv("API_KEY")
API_URL = "https://www.goodreads.com/book/review_counts.json"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        form = request.form.to_dict()
        # Ensure proper form
        verified = verify_form(form, ["username", "password", "confirmation"])
        if verified is not None:
            return verified, 400

        elif form.get("password") != form.get("confirmation"):
            return "passwords don't match", 400

        if db.execute("SELECT * FROM users WHERE username = :username",
                      form).fetchone() is not None:
            return "this username is taken", 400

        form["hashed"] = generate_password_hash(form.get("password"))

        db.execute("""INSERT INTO users (username, password_hash)
                   VALUES (:username, :hashed)""",
                   form)
        db.commit()

        return redirect("/login")

    else:

        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        form = request.form.to_dict()
        # Ensure username and password were submitted
        verified = verify_form(form, ["username", "password"])
        if verified is not None:
            return verified, 403

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          form).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
                rows[0]["password_hash"], form["password"]):
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
    if request.method == "POST":

        form = request.form.to_dict()
        verified = verify_form(form, ["query"])
        if verified is not None:
            return verified, 403

        # PostgreSQL FTS
        # TODO consider indexing
        form["query"] = form["query"].replace(" ", "&")
        rows = db.execute("""SELECT b.title, b.year, b.isbn, a.name AS author
                        FROM books b, authors a WHERE a.id = b.author_id AND
                        to_tsvector(title||' '||name||' '||year||' '||isbn)
                        @@ to_tsquery(:query)""", form).fetchall()

        return render_template("search.html", rows=rows)

    else:
        return render_template("search.html")


@app.route("/books/<isbn>")
def books(isbn):

    book = db.execute("""SELECT b.title, b.year, b.isbn, a.name AS author,
                    to_char(AVG(r.rating), '0.00') AS rating,
                    COUNT(r.rating) AS count
                    FROM books b INNER JOIN authors a ON b.author_id = a.id
                    LEFT OUTER JOIN reviews r ON b.isbn = r.book_isbn
                    WHERE b.isbn = :isbn GROUP BY title, year, isbn, author""",
                      {"isbn": isbn}).fetchone()

    if book is None:
        raise default_exceptions[404]

    if book["count"] != 0:
        reviews = db.execute("""SELECT r.rating, r.review
                        FROM reviews r WHERE r.book_isbn = :isbn""",
                             {"isbn": isbn}).fetchall()
    else:
        reviews = None

    goodreads = requests.get(API_URL, params={"key": API_KEY, "isbns": isbn})
    goodreads = goodreads.json()["books"][0]

    return render_template("book_page.html", book=book, reviews=reviews,
                           goodreads=goodreads)


@app.route("/review/<isbn>", methods=["POST"])
def review(isbn):
    if session.get("user_id") is None:
        return "Must be logged in"

    parameters = {
        "user_id": session["user_id"],
        "isbn": isbn
    }

    # TODO these two checks are possible in one DB-query
    existing = db.execute("""SELECT * FROM reviews WHERE user_id = :user_id
                AND book_isbn = :isbn""", parameters).rowcount
    # TODO save text and rate, offer rewrite
    if existing != 0:
        return "You already reviewed this book"

    # TODO function to confirm book is real
    book = db.execute("""SELECT * FROM books
                    WHERE isbn = :isbn""", parameters).rowcount
    if book != 1:
        raise default_exceptions[404]

    # TODO "must provide"? Appropriate message please
    form = request.form.to_dict()
    verified = verify_form(form, ["rating", "review_text"])
    if verified is not None:
        return verified, 403

    parameters.update(form)

    db.execute("""INSERT INTO reviews(rating, review, user_id, book_isbn)
            VALUES(:rating, :review_text, :user_id, :isbn)""", parameters)
    db.commit()

    return redirect(f"/books/{isbn}")


@app.route("/api/<isbn>")
def api():
    return jsonify(None)


def errorhandler(error):
    return render_template("error_render.html", error=error), error.code


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


# TODO flashing messages
def verify_form(a_form, items):
    for item in items:
        if a_form.get(item) in (None, ""):
            if item == "confirmation":
                return "must re-enter password"
            else:
                return f"must provide {item}"
    return None
