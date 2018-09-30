import os
import argparse

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker

# TODO rename to "database.py", use as package for application?


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-rw", "--rewrite",
                        help="rewrite the database",
                        action="store_true")
    args = parser.parse_args()
    if args.rewrite:
        drop_tables()

    try:
        db.execute("""CREATE TABLE authors(id SERIAL PRIMARY KEY,
            name VARCHAR UNIQUE NOT NULL)""")
        db.execute("""CREATE TABLE books(isbn VARCHAR UNIQUE,
            title VARCHAR NOT NULL, year INTEGER NOT NULL,
            author_id INTEGER REFERENCES authors)""")
        db.execute("""CREATE TABLE users(id SERIAL PRIMARY KEY,
            username VARCHAR, password_hash VARCHAR)""")
        db.execute("""CREATE TABLE reviews(rating INTEGER NOT NULL,
            review VARCHAR, user_id INTEGER REFERENCES users)""")
    except(exc.ProgrammingError):
        # TODO likely more possible reasons
        print("It appears tables are already created.\n Use -rw flag")
        return 1
    db.commit()
    print("Database successfully initiated")
    return None


# TODO hardcoded stuff
def drop_tables():
    for table in ["books", "authors", "reviews", "users"]:
        db.execute(f"DROP TABLE {table}")
    db.commit()
    print("Successfully dropped")
    return None


if __name__ == "__main__":
    main()
