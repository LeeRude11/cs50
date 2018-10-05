import os

from flask import (Flask, session, jsonify, redirect, request, render_template,
                   flash, abort)
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

        form, flashed = verify_and_return_form(["username", "password",
                                                "confirmation"])
        if flashed is True:
            return render_template("register.html"), 401

        if db.execute("SELECT * FROM users WHERE username = :username",
                      form).fetchone() is not None:
            flash("This username is taken")
            return render_template("register.html"), 401

        form["hashed"] = generate_password_hash(form["password"])

        db.execute("""INSERT INTO users (username, password_hash)
                   VALUES (:username, :hashed)""",
                   form)
        db.commit()

        flash("Successfully registered")

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

        form, flashed = verify_and_return_form(["username", "password"])
        if flashed is True:
            return render_template("login.html"), 401

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          form).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
                rows[0]["password_hash"], form["password"]):
            return "invalid username and/or password", 401

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        flash(f"Logged in as {session['username']}")

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    return redirect(request.referrer or "/")


@app.route("/search", methods=["GET", "POST"])
def search():
    """Find a book by its title, author's name, isbn or realease year"""

    if request.method == "POST":

        form, flashed = verify_and_return_form(["query"])
        if flashed is True:
            return render_template("search.html"), 401

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


@app.route("/api/<isbn>", endpoint="api")
@app.route("/books/<isbn>", endpoint="books")
def books(isbn):
    """Return book's info in either JSON or rendered Jinja template"""

    book = db.execute("""SELECT b.title, b.year, b.isbn, a.name AS author,
                    to_char(AVG(r.rating), 'FM0.00') AS average_rating,
                    COUNT(r.rating) AS review_count
                    FROM books b INNER JOIN authors a ON b.author_id = a.id
                    LEFT OUTER JOIN reviews r ON b.isbn = r.book_isbn
                    WHERE b.isbn = :isbn GROUP BY title, year, isbn, author""",
                      {"isbn": isbn}).fetchone()

    if book is None:
        abort(404)

    if request.endpoint == "api":
        return jsonify(dict(book))

    if book["review_count"] != 0:
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
    """Let users post a review of the book"""

    if session.get("user_id") is None:
        abort(403)

    parameters = {
        "user_id": session["user_id"],
        "isbn": isbn
    }

    book_and_review = db.execute("""SELECT b.isbn, r.user_id FROM books b
            LEFT OUTER JOIN reviews r
            ON (b.isbn = r.book_isbn AND r.user_id = :user_id)
            WHERE b.isbn = :isbn""", parameters).fetchone()

    if book_and_review is None:
        abort(404)
    if book_and_review["user_id"] is not None:
        # TODO save text and rate, offer rewrite
        flash("You already reviewed this book")
        return redirect(f"/books/{isbn}")

    form, flashed = verify_and_return_form(["rating", "review_text"])
    if flashed is True:
        # TODO 401? Render but not redirect
        return redirect(f"/books/{isbn}")

    parameters.update(form)

    db.execute("""INSERT INTO reviews(rating, review, user_id, book_isbn)
            VALUES(:rating, :review_text, :user_id, :isbn)""", parameters)
    db.commit()

    flash("Successfully published a review!")
    return redirect(f"/books/{isbn}")


def errorhandler(error):
    """Use a Jinja2 template to inform about errors"""

    return render_template("error_render.html", error=error), error.code


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


MISSING_MESSAGES = {
    "confirmation": "Must re-enter password",
    "mismatch": "Passwords don't match",
    "rate": "Book rating is required for a review",
    "review_text": "Can't submit empty reviews"
}


def verify_and_return_form(items):
    form = request.form.to_dict()
    flashed = False
    for item in items:
        if form.get(item) in (None, ""):
            flash(MISSING_MESSAGES.get(item) or f"Must provide {item}")
            flashed = True
            break
    else:
        conf = "confirmation"
        if (conf in items and form["password"] != form[conf]):
            flash(MISSING_MESSAGES["mismatch"])
            flashed = True

    return form, flashed
