import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

print("Database URL environment variable correctly set.")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
print("Database is set up.")

# Initialize tables
# timestamp is seconds from 1970 (Unix time).  INT will get to 2038, but might as well go forever with BIGINT :-)
db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, password VARCHAR NOT NULL);")
db.execute("CREATE TABLE reviews (id SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL, review VARCHAR NOT NULL, rating INTEGER NOT NULL, username VARCHAR NOT NULL, timestamp BIGINT NOT NULL);") # So many sites recommended always having a primary key, even if it's an artificial abstraction.
db.execute("CREATE TABLE books (isbn VARCHAR PRIMARY KEY, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year VARCHAR NOT NULL);")
db.execute("CREATE TABLE quotes (id SERIAL PRIMARY KEY, quote VARCHAR NOT NULL, source VARCHAR NOT NULL);")
print("Tables initialized.")

# Open the provided books.csv file
f=open("books.csv", "r")
reader = csv.reader(f)
print("Opening books.csv for import...")
for isbn, title, author, year in reader:
    # skip the entry if it's the header
    if isbn == "isbn":
        pass
    else:
        # add the CSV table data to my SQL database
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:a, :b, :c, :d);", {"a":isbn,"b":title,"c":author,"d":year})

"Books imported, committing changes..."
f.close()
db.commit()
print("")

# Add quotes on books as well
f=open("quotes_on_books.csv", "r")
reader = csv.reader(f)
print("Opening quotes_on_books.csv for import...")
for quote, source in reader:
    # skip the entry if it's the header
    if quote == "quote":
        pass
    else:
        # add the CSV table data to my SQL database
        db.execute("INSERT INTO quotes (quote, source) VALUES (:a, :b);", {"a":quote,"b":source})

"Quotes imported, committing changes..."
f.close()
db.commit()

# Add a few default users to test with
# https://stackoverflow.com/questions/37970743/unique-violation-7-error-duplicate-key-value-violates-unique-constraint-users/37972960#37972960
# First my code failed because I added users through Adminer (which did not increment id pointer)
print("Adding some default users to DB...")
db.execute("INSERT INTO users (username, password) VALUES ('Joel', '7');")
db.execute("INSERT INTO users (username, password) VALUES ('Michelle', '14');")
db.execute("INSERT INTO users (username, password) VALUES ('Molina', '165');")
db.execute("INSERT INTO users (username, password) VALUES ('Ellie', '3');")
db.execute("INSERT INTO users (username, password) VALUES ('Izzy', '1');")
db.commit()

# Add a few initial reviews
print("Seeding some initial reviews...")
db.execute("INSERT INTO reviews (isbn, review, rating, username, timestamp) VALUES ('030734813X', 'Best book ever!', 5, 'Joel', 1568316549);")
db.execute("INSERT INTO reviews (isbn, review, rating, username, timestamp) VALUES ('0316015849', 'This book got me into reading!', 5, 'Michelle', 1568316549);")
db.commit()

print("Book, quotes, reviews, and user imports complete.")