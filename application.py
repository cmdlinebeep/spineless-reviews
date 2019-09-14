import os
from datetime import datetime
import requests

from flask import Flask, session, render_template, redirect, url_for, request, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from functools import wraps

app = Flask(__name__)

# Check for environment variable for DB
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Check for GoodReads API key
if not os.getenv("GOODREADS_API_KEY"):
    raise RuntimeError("GOODREADS_API_KEY is not set")

# Don't get this over and over and over
gr_key = os.getenv("GOODREADS_API_KEY")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

year = datetime.now().year

# See https://flask.palletsprojects.com/en/1.0.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect( url_for('index') )
        return f(*args, **kwargs)
    return decorated_function


def get_goodreads_review(isbn):
    """Returns the average rating and number of ratings a book has received by Goodreads"""
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": gr_key, "isbns": isbn})
    # Typical response for res.json():
    # {'books': [{'id': 7677, 'isbn': '030734813X', 'isbn13': '9780307348135', 'ratings_count': 451949, 'reviews_count': 543831, 'text_reviews_count': 3625, 'work_ratings_count': 742526, 'work_reviews_count': 568967, 'work_text_reviews_count': 10774, 'average_rating': '4.01'}]}
    res = res.json()
    avg_rating = res['books'][0]['average_rating']          # API returns a weird nested list 
    num_ratings = res['books'][0]['work_ratings_count']
    return avg_rating, num_ratings


def stars_to_int(star_review):
    if   star_review == '★☆☆☆☆':
        stars_int = 1
    elif star_review == '★★☆☆☆':
        stars_int = 2
    elif star_review == '★★★☆☆':
        stars_int = 3
    elif star_review == '★★★★☆':
        stars_int = 4
    elif star_review == '★★★★★':
        stars_int = 5
    else:
        print("Error in stars_to_int()!")
    return stars_int


def int_to_stars(stars_int):
    if   stars_int == 1:
        star_review = '★☆☆☆☆'
    elif stars_int == 2:
        star_review = '★★☆☆☆'
    elif stars_int == 3:
        star_review = '★★★☆☆'
    elif stars_int == 4:
        star_review = '★★★★☆'
    elif stars_int == 5:
        star_review = '★★★★★'
    else:
        print("Error in int_to_stars()!")
    return star_review


def get_pretty_date(timestamp):
    """ 1568316549  -->  'Sep 12, 2019' (We don't care about the time of day someone left a review)"""
    # now = datetime.now()
    # now  is datetime(2019, 9, 12, 13, 8, 14, 162166)
    # str = now.strftime("%b") + " " + now.strftime("%d") + ", " + now.strftime("%Y")
    # 'Sep 12, 2019'   (we don't care about the time of day someone left a review)
    date = datetime.fromtimestamp( int(timestamp) )
    pretty_date = date.strftime("%b") + " " + date.strftime("%d") + ", " + date.strftime("%Y")
    return pretty_date


@app.route("/register", methods=["POST"])
def register():
    # Grab values from submission form
    username = request.form.get("username")
    password = request.form.get("password")
    repeat_password = request.form.get("repeat_password")

    # Two alternative ways to do what I'm trying to do, since I really want a redirect not a render on bad login
    # (render on bad login keeps them on <site>/login page)

    # NOTE: Passing arguments while doing redirect using session cookie
    # https://stackoverflow.com/questions/17057191/redirect-while-passing-arguments

    # NOTE: Also can try message flashing, https://flask.palletsprojects.com/en/1.1.x/patterns/flashing/   --> Just do flashing, less buggy and less flashy than modals.  Easier to add new ones too.

    # Check if any of the data in the form was missing
    if not username or not password or not repeat_password:
        flash('All fields are required.  Please try again.', 'text-danger')
        return redirect( url_for('index') )

    # Check if username already exists in database
    check_user = db.execute("SELECT * FROM users WHERE username = :a", {"a": username}).fetchone()
    if check_user:
        flash('That username is taken!  Please try again.', 'text-danger')
        return redirect( url_for('index') )
    
    # Check if passwords are mismatched
    if password != repeat_password:
        flash('Passwords must match.', 'text-danger')
        return redirect( url_for('index') )

    # If still good, add new user to database
    db.execute("INSERT INTO users (username, password) VALUES (:a, :b);", {"a":username, "b":password})
    
    # Need to commit edits, just in memory at the moment
    db.commit()

    flash('Thanks for registering!  You can now sign in.', 'text-success')
    return redirect( url_for('index') )


@app.route("/login", methods=["POST"])
def login():
    # Forget any user ID 
    session.clear()

    username = request.form.get("username")
    password = request.form.get("password")

    # Check if user or password are blank
    if not username or not password:
        flash('Username and password are required, please try again.', 'text-danger')
        return redirect( url_for('index') )
    
    # Check if user credentials match
    # NOTE: In production code, the passwords would be salted and hashed.
    auth_user = db.execute("SELECT * FROM users WHERE username = :a AND password = :b;", {"a": username, "b": password}).fetchone()
    if auth_user is None:
        flash('Incorrect username or password, please try again.', 'text-danger')
        return redirect( url_for('index') )

    else:
        # There was a user whose name and password matched what was entered, log them in.
    
        # Save which user is logged in
        session["user_id"] = username

        # Spouse A/B testing indicates this is more clear with no search results than the search page :-)
        return redirect( url_for('index') )


@app.route("/logout", methods=["GET", "POST"])
def logout():
    # POST from the "Switch Users" button when you're already logged in, since a form
    # GET from the normal Sign Out redirect in the upper corner

    # Forget any user ID 
    session.clear()

    return redirect( url_for('index') )


@app.route("/")
def index():
    # Get a random quote about books to serve up
    row = db.execute("SELECT quote, source FROM quotes ORDER BY RANDOM() LIMIT 1;").fetchone()
    quote=row[0]
    quote_source=row[1]

    # Use session.get("user_id") instead of session["user_id"] so don't get KeyError if user is None
    return render_template("index.html", quote=quote, quote_source=quote_source, year=year, user=session.get("user_id"))


# See https://flask.palletsprojects.com/en/1.0.x/patterns/viewdecorators/
# Need to allow both methods though, because the Login route sends us here via GET, not POST
@app.route("/search", methods=["POST", "GET"])
@login_required
def search():

    books = []      # This is filled in based on the query, is a list of dictionary objects
    query = None

    #book1 = {"title": "Jurassic Pork", "author": "Piggly Wiggly", "year": "1978", "isbn": "xyz"}
    #book2 = {"title": "Congo Line", "author": "M.C. Dancer", "year": "1983", "isbn": "abc"}
    #books = [book1, book2]

    # NOTE: Not sure I need to differentiate these yet
    if request.method == "POST":
        # User submitted a search form
        query = request.form.get("query")

        # Strip leading and trailing whitespace, and normalize any spaces in between to one space 
        # (otherwise multiple spaces between words would fail search)
        query = " ".join(query.split())

        # Make sure search is at least 4 chars long or results will be too noisy
        if len(query) < 4:
            flash('Search query must be at least 4 letters long.', 'text-danger')
            return render_template("search.html", year=year, user=session.get("user_id"), books=books, query=query)

        # Need wildcard to search the database on a partial match
        # query = '%' + query + '%' --> See below
    
        # Case Insensitive search
        # https://stackoverflow.com/questions/7005302/postgresql-how-to-make-case-insensitive-query
        # Chose this way (ILIKE) with high performance penalty to prioritize UX instead (they can type any capitalization)
        rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                            isbn ILIKE :query OR \
                            title ILIKE :query OR \
                            author ILIKE :query LIMIT 10",
                            {"query": "%" + query + "%"})   # Append wildcards to search the database on a partial match
                                                            # Doing this way instead of modfying query, so they don't print on no search matches

        # Add each resulting row into the books dictionary
        for row in rows.fetchall():
            book = { "isbn": row[0], "title": row[1], "author": row[2], "year": row[3] }
            books.append(book)

    return render_template("search.html", year=year, user=session.get("user_id"), books=books, query=query)


@app.route("/book/<isbn>", methods=["POST", "GET"])
@login_required
def book(isbn):
    #if request.method == "GET":
    # We get here via link from book card on search results page or if they type the ISBN into the URL directly

    # Grab data on the book
    # This needs to come first, as a user leaving a review accesses the book variable
    row = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :a",
                        {"a": isbn}).fetchone()

    # If there are no results (user types in a bad ISBN into URL), should 404
    if not row:
        # Book doesn't exist
        flash('Invalid URL. Did you type in a non-existent ISBN?', 'text-danger')
        return redirect( url_for('search') )

    book = { "isbn": row[0], "title": row[1], "author": row[2], "year": row[3] }

    if request.method == "POST":
        # We get here if the user leaves a review (through submission form)
        
        # User submitted a review through the form
        text_review = request.form.get("text_review")
        star_review = request.form.get("star_review")   # This is saved as an integer in the database, so we'll need to convert back and forth, unfortunately
        
        # Convert star rating to int, e.g. "★★★☆☆" --> 3
        stars_int = stars_to_int(star_review)
                
        # Get timestamp of comment (Unix seconds since 1970)
        timestamp = int( datetime.timestamp(datetime.now()) )
        
        # Add the review to the database
        db.execute("INSERT INTO reviews (isbn, review, rating, username, timestamp) VALUES (:a, :b, :c, :d, :e);", {"a":book['isbn'], "b":text_review, "c":stars_int, "d":session.get("user_id"), "e":timestamp})
        db.commit()

    # Grab the Goodreads API data (avg_rating is a string and num_ratings is integer) and add to book object
    gr_avg_rating, gr_num_ratings = get_goodreads_review(book["isbn"])
    book['gr_avg_rating'] = gr_avg_rating
    book['gr_num_ratings'] = gr_num_ratings

    # Pass in the rating rounted to integer number of stars
    book['num_stars'] = round( float(gr_avg_rating) )

    reviews = []    # List of dictionary items if there are any, otherwise this evaluates to None

    # Finds any reviews left by user
    check_user_review = db.execute("SELECT review, rating, username, timestamp FROM reviews WHERE isbn = :a AND username = :b;", {"a": book['isbn'], "b": session.get("user_id") }).fetchone()

    user_review = None
    if check_user_review:
        # Convert review in int back to star text
        star_rating = int_to_stars(check_user_review[1])

        # And pretty date of user comment
        pretty_date = get_pretty_date(check_user_review[3])

        user_review = {"review": check_user_review[0], "star_rating": star_rating, "pretty_date": pretty_date}

    # Finds any reviews left by all users
    all_reviews = db.execute("SELECT review, rating, username, timestamp FROM reviews WHERE isbn = :a;", {"a": book['isbn']}).fetchall()

    # Add any reviews to the reviews list
    for row in all_reviews:
        # Convert review in int back to star text
        star_rating = int_to_stars(row[1])

        # And pretty date of user comment
        pretty_date = get_pretty_date(row[3])

        review = {"review": row[0], "star_rating": star_rating, "username": row[2], "pretty_date": pretty_date}
        reviews.append(review)

    return render_template("book.html", year=year, user=session.get("user_id"), book=book, reviews=reviews, user_review=user_review)    


@app.route("/api/<isbn>", methods=["GET"])
@login_required
def api(isbn):
    # Only GET method is valid, by calling URL via API call

    # Punted on trying to do this with a JOIN statement.  Got it partially working, but couldn't get it to work if there were no reviews.
    # Instead just doing two DB queries.
    row = db.execute("SELECT title, author, year FROM books \
                        WHERE isbn = :a GROUP BY title, author, year;", {"a": isbn}).fetchone()

    # If there are no results (user types in a bad ISBN into URL), should 404
    if not row:
        # Book doesn't exist
        return render_template('404.html'), 404

    # Got a valid response.  Convert to dictionary.
    # NOTE: Assignment wants year as an int, not a string.
    book_dict = { "isbn": isbn, "title": row[0], "author": row[1], "year": int(row[2]) }

    # Now look for any reviews (could be none)
    row = db.execute("SELECT COUNT(reviews.id), AVG(reviews.rating) FROM reviews \
                        WHERE isbn = :a;", {"a": isbn}).fetchone()

    # => SELECT COUNT(reviews.id), AVG(reviews.rating) FROM reviews WHERE isbn = '1250012570';
    # count | avg
    # -------+-----
    #     0 |
    # (1 row)

    # => SELECT COUNT(reviews.id), AVG(reviews.rating) FROM reviews WHERE isbn = '030734813X';
    # count |        avg
    # -------+--------------------
    #     2 | 3.0000000000000000
    # (1 row)

    book_dict['review_count'] = row[0]
    if row[0] == 0:
        book_dict['average_score'] = 0.0
    else:
        book_dict['average_score'] = float('%.2f'%row[1])       # Round average to hundredths digit
    
    return jsonify(book_dict)