# --------------------Using SQLALCHEMY-------------------------#
from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import Table, Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

app = Flask(__name__)

##CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///playground.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Owner(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    address = Column(String(100))
    pets = relationship('Pet', back_populates='owner')


class Pet(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    age = Column(Integer)
    owner_id = Column(Integer, ForeignKey('owner.id'))
    owner = relationship('Owner', back_populates='pets')

jack = Pet(name="jack", age=23, owner=emmanuel)
db.session.add(jack)
db.session.commit()





# ##CREATE TABLE
# class User(UserMixin, db.Model):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, nullable=False)
#     email = Column(String(100), unique=True)
#     password = Column(String(100), nullable=False)
#     name = Column(String(100), nullable=False)
#
#
# # This will act like a List of BlogPost objects attached to each User.
# # The "author" refers to the author property in the BlogPost class.
#     posts = relationship("BlogPost", back_populates="author")
#
#
# class BlogPost(db.Model):
#     __tablename__ = "blog_posts"
#     id = Column(Integer, primary_key=True)
#
#     # Create Foreign Key, "users.id" the users refers to the tablename of User.
#     author_id = Column(Integer, ForeignKey("users.id"))
#     # Create reference to the User object, the "posts" refers to the posts property in the User class.
#     author = relationship("User", back_populates="posts")
#
#     title = Column(String(250), unique=True, nullable=False)
#     subtitle = Column(String(250), nullable=False)
#     date = Column(String(250), nullable=False)
#     body = Column(Text, nullable=False)
#     img_url = Column(String(250), nullable=False)


db.create_all()
