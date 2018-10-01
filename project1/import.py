import csv
import os
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    # ensure input file is provided
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="input .csv file")
    args = parser.parse_args()
    if os.path.isfile(args.input) is False:
        print("Input file was not found")
        return 1

    parse_csv_w_function(args.input, write_book_to_db)
    db.commit()


def write_book_to_db_old(entry):
    # add author if he is not in database
    # TODO return author_id from query?
    # on conlficl the id is still assigned, many spaces in indices
    db.execute("""INSERT INTO authors(name) VALUES(:name)
               ON CONFLICT DO NOTHING""",
               {"name": entry["author"]})
    db.execute("""INSERT INTO books(isbn, title, year, author_id)
               VALUES(:isbn, :title, :year,
               (SELECT id FROM authors WHERE name=:author))""",
               entry)
    return None


# https://dba.stackexchange.com/a/46477
# add book and add author if not present
def write_book_to_db(entry):
    db.execute("""WITH sel AS (
       SELECT entry.isbn, entry.title, entry.year, entry.name,
       authors.id AS author_id
       FROM  (
          VALUES
             (text :isbn, text :title, integer :year, text :author)
          ) entry (isbn, title, year, name)
       LEFT JOIN authors USING (name)
       )
    , ins AS (
       INSERT INTO authors (name)
       SELECT name FROM sel WHERE author_id IS NULL
       RETURNING id AS author_id, name
       )
    INSERT INTO books (isbn, title, year, author_id)
    SELECT sel.isbn, sel.title, sel.year,
    COALESCE(sel.author_id, ins.author_id)
    FROM sel
    LEFT JOIN ins USING (name)""", entry)


def parse_csv_w_function(csv_name, apply_func):
    # TODO general function to get dicts based on first row headers
    with open(csv_name) as csv_file:
        entries = csv.reader(csv_file)
        headers = entries.__next__()
        # TODO pass generator to query execute many? timeit
        for entry in entries:
            entry_dict = dict(zip(headers, entry))
            # TODO here I pass dict to DB INPUT function
            # when this whole function exits, call db.commit()
            apply_func(entry_dict)


if __name__ == "__main__":
    main()
