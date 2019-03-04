import os
import math
import requests
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import xml.etree.ElementTree as ET
from datetime import datetime
app = Flask(__name__)

# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://url")
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    if not session.get("logged_in"):
        return render_template("login.html")
    else:
        return render_template("home.html")

@app.route("/home", methods=["GET","POST"])
def home():
    if request.method == "GET":
        if not session.get("logged_in"):
            return render_template("login.html")
        else:
            return render_template("home.html")
    if request.method == "POST":
        text = request.form.get("query").lower()

        if text:
            results = db.execute("SELECT * FROM books WHERE lower(isbn) LIKE :isbn or lower(title) LIKE :title OR lower(author) LIKE :author OR year LIKE :year",{"isbn": '%'+text+'%', "title": '%'+text+'%', "author": '%'+text+'%', "year": '%'+text+'%'}).fetchall()
            if results:
                return render_template("home.html", results=results)
            else:
                return render_template("home.html", message="No Results Found")
        else:
            return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        if session.get("logged_in"):
            return redirect(url_for('home'), "303")
        else:
            return render_template("login.html", message="Enter your Username and Password")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        rs = db.execute("SELECT password FROM users WHERE username = :username",{"username" : username})

        if not rs:
            return render_template("login.html", message="Invalid Username or Password")

        for res in rs:
            if password == res[0]:
                session["logged_in"] = True
                session["user_name"] = username
                return redirect(url_for('index'))
        else:
            return render_template("login.html", message="Invalid Username or Password")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "GET":
        if session.get("logged_in"):
            return redirect(url_for('home'), "303")
        else:
            return render_template("signup.html")
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        db.execute("INSERT INTO users (username, password, email) VALUES(:username, :password, :email)",{"username" : username, "password" : password, "email": email})
        db.commit()
        return redirect(url_for('login'))


@app.route("/logout")
def logout():
   session["logged_in"] = False
   session["user_name"] = None
   return redirect(url_for('login'))



@app.route("/book", methods=["GET"])
def book():
    if request.method == "GET":
        if session.get("logged_in"):
            bkisbn=request.args.get('bkisbn')
            book_id=request.args.get('book_id')
            res = requests.get("https://www.goodreads.com/book/isbn/"+bkisbn+".xml",params={"key": "***************"})
            rev = ET.fromstring(res.text)
            resdb = db.execute("SELECT * FROM reviews WHERE username = :username and book_id = :book_id",{"username":session["user_name"], "book_id": book_id}).fetchone()
            print(resdb)
            return render_template("book.html", review=rev, ressdb=resdb, username=session["user_name"].title())
        else:
            return render_template("login.html")


@app.route("/review/<string:bkisbn>,<int:book_id>", methods=["GET","POST"])
def review(bkisbn,book_id):
    if request.method == "GET":
        if session.get("logged_in"):
            return redirect(url_for('home'), "303")
        else:
            return redirect(url_for('login'))
    if request.method == "POST":
        rating = request.form.get("rating")
        review = request.form.get("comment")
        username = session["user_name"]
        rating_time = datetime.date(datetime.now())
        db.execute("INSERT INTO reviews (book_id, username, isbn, comment, rating, rating_time) VALUES(:book_id, :username, :isbn, :comment, :rating, :rating_time)",{"book_id":book_id, "username": username, "isbn": bkisbn, "comment": review, "rating": rating, "rating_time": rating_time})
        db.commit()
        return redirect(url_for('book',bkisbn = bkisbn, book_id = book_id))


@app.route("/api/<isbn>")
def api(isbn):
    rs1=db.execute("SELECT title,author,year,isbn FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    rs2=db.execute("SELECT COUNT(review_id), AVG(rating) FROM reviews WHERE isbn = :isbn",{"isbn":isbn}).fetchall()
    if rs1 and rs2 is None:
        return jsonify({"error": "Invalid isbn"}), 422
    avg=math.floor(rs2[0][1])
    return jsonify(
    {
        "title": rs1.title,
        "author": rs1.author,
        "year": rs1.year,
        "isbn": rs1.isbn,
        "review_count": rs2[0][0],
        "average_score": avg
    })
