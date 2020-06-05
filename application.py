import os, requests

from flask import Flask, session, render_template, request, url_for, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

app.secretKey = b'_5#y2L"F4Q8z\n\xec]/'

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

@app.route("/", methods = ['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.pop('username', None)
        username = request.form.get("username")
        password = request.form.get("password")
        if db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
        {"username": username, "password": password}).rowcount == 0:
            return render_template ("error.html", message="Invalid username/password")
        else:
            session['username']  = username
            return redirect(url_for('search'))

    return render_template("index.html")

@app.route("/registration", methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if db.execute("SELECT username FROM users WHERE username = :username",
        {"username": username}).rowcount == 1:
            return render_template ("error.html", message="Username unavailable")
        else:
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
            {"username": username, "password": password})
            db.commit()
            return render_template ("error.html", message="Registration successful")

    return render_template("registration.html")

@app.route("/searchPage")
def search():
    return render_template("search.html")

@app.route("/searchResults", methods=["POST"])
def searchDB():
    if request.method == "POST":
        searchParam = request.form.get("choices-single-defaul")
        searchField = request.form.get("searchField")
        if searchParam == "ISBN":
            searchResults = db.execute("SELECT * FROM books WHERE UPPER (isbn) LIKE UPPER (:searchField)",
            {"searchField": "%" + searchField + "%" }).fetchall()
        elif searchParam == "Book Title":
            searchResults = db.execute("SELECT * FROM books WHERE UPPER (title) LIKE UPPER (:searchField)",
            {"searchField": "%" + searchField + "%" }).fetchall()
        else:
            searchResults = db.execute("SELECT * FROM books WHERE UPPER (author) LIKE UPPER (:searchField)",
            {"searchField": "%" + searchField + "%" }).fetchall()

    return render_template("searchResult.html", searchResults=searchResults)

@app.route("/books/<ISBN>", methods=["GET", "POST"])
def bookTitle(ISBN):

    #Retrieving book information from the database
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
    {"isbn": ISBN}).fetchone()

    #Retrieving review data from www.goodreads.com
    res=requests.get("https://www.goodreads.com/book/review_counts.json", params = {"key": "6RIbwG1Jzy093AMLpfSo1g", "isbns": ISBN})
    data = res.json()
    numRatings = data["books"][0]["ratings_count"]
    avgRating = data["books"][0]["average_rating"]

    #Grabbing all the reviews from the database for the current book
    reviews = db.execute("SELECT username, review FROM reviews WHERE isbn = :isbn",
    {"isbn": ISBN}).fetchall()

    #Checking to see if the current user already posted a review for the current book
    reviewedByUser = False
    if db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username = :username",
    {"isbn": ISBN, "username": session['username']}).rowcount > 0:
        reviewedByUser = True

    #Generating page for the current book
    return render_template("booksTemplate.html", reviewedByUser = reviewedByUser, authorName=book.author, pubYear=book.year, isbn=book.isbn, bookTitle=book.title, avgRating = avgRating, numRatings = numRatings, reviews = reviews)

@app.route("/submitReview/<ISBN>", methods=["POST"])
def createReview(ISBN):
    if request.method == "POST":
        username = session['username']
        review = request.form.get("review")
        db.execute("INSERT INTO reviews VALUES (:isbn, :username, :review)",
        {"isbn": ISBN, "username": username, "review": review})
        db.commit()
    return render_template("error.html", message="Review Posted!")
