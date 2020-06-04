import os, requests

from flask import Flask, session, render_template, request
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
    return render_template("index.html")

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

@app.route("/books/<ISBN>")
def bookTitle(ISBN):

    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
    {"isbn": ISBN}).fetchone()

    res=requests.get("https://www.goodreads.com/book/review_counts.json", params = {"key": "6RIbwG1Jzy093AMLpfSo1g", "isbns": ISBN})
    data = res.json()
    numRatings = data["books"][0]["ratings_count"]
    avgRating = data["books"][0]["average_rating"]

    return render_template("booksTemplate.html", authorName=book.author, pubYear=book.year, isbn=book.isbn, bookTitle=book.title, avgRating = avgRating, numRatings = numRatings)
