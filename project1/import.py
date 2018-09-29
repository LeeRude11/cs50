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
    parse_csv_w_function(os.input, write_book_to_db)


def write_book_to_db(entry):
    return None


def parse_csv_w_function(csv_name, apply_func):
    # TODO general function to get dicts based on first row headers
    with open(csv_name) as csv_file:
        entries = csv.reader(csv_file)
        headers = entries.__next__()
        for entry in entries:
            entry_dict = dict(zip(headers, entry))
            # TODO here I pass dict to DB INPUT function
            # when this whole function exits, call db.commit()
            apply_func(entry_dict)
