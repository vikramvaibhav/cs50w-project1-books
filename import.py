import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgres://kgwqiphwhnpdqk:1c5301d02e776d24903d24050de6e288c5fd577ef4032b11ba47c7fdb37c0018@ec2-54-235-67-106.compute-1.amazonaws.com:5432/d6jpt443rsts8g")
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Book Added ISBN: {isbn} Title: {title} Author: {author} Year: {year} ")
    db.commit()

if __name__ == "__main__":
    main()
