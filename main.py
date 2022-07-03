from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
'''________________________________________________________'''
from datetime import date
import os
'''________________________________________________________'''
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from sqlite3 import IntegrityError
'''________________________________________________________'''
from functools import wraps
from flask import abort
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship
'''________________________________________________________'''
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URL'] = os.environ.get("DATABASE_URL")
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# it is called a hook function by the login manager. it helps us to  trust it all custom code to validate or reject a
# user access
login_manager = LoginManager()
login_manager.init_app(app)

# Creating a Gravatar
gravatar = Gravatar(app, size=500, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create aadmin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


##CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    password = Column(String(100))
    name = Column(String(100))
    # this line of code tend to form a relationship btw BlogPost and it back_populates a author in which it creates
    # an imaginary column in our BlogPost Section
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True)
    # "users.id" The users refers to the tablename of the Users class.
    # "posts" refers to the comments property in the User class.
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = Column(String(250), unique=True, nullable=False)
    subtitle = Column(String(250), nullable=False)
    date = Column(String(250), nullable=False)
    body = Column(Text, nullable=False)
    img_url = Column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    text = Column(String(250), nullable=False)
    # "users.id" The users refers to the tablename of the Users class.
    # "comments" refers to the comments property in the User class.
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="comments")
    # "blog_post.id" The blog_post refers to the tablename of the BlogPost class.
    # "parent_post" refers to the parent_post property in the BlogPost class.
    post_id = Column(Integer, ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


db.create_all()

'''
we are have problem in this part where after login as an admin if we hit the home tab again it will got back to the user 
we need to fix it 
'''


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    # this line of code tend to get the user id after we have log in to the page,
    # it is being gotten from the login() function that  was pass to the get_all_post() in the redirect
    return render_template("index.html", all_posts=posts, current_user=current_user, current_year=date.today().year)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash_and_salted_password = generate_password_hash(
            request.form.get("password"),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            flash("log in with your email because you are already registered")
            return redirect(url_for('login'))
        else:
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form, current_user=current_user, current_year=date.today().year)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = request.form.get("email")
        password = request.form.get("password")

        # get all content of email in user table in our database
        user = User.query.filter_by(email=email).first()

        # validation of email
        if not user:
            flash("Your email does not exist, please try again.")
        # validation of password
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, Please try again")
        else:
            # this code give access to user that have been validated
            login_user(user)

            return redirect(url_for('get_all_posts', user_id=user.id))
    return render_template("login.html", form=form, current_user=current_user,current_year=date.today().year)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if form.validate_on_submit():
        # it check if the user is sign in, else redirect to create a account or log in
        if not current_user.is_authenticated:
            flash("Log in or you register a new account to comment")
            return redirect(url_for('login'))

        # adding comment to our database
        new_comment = Comment(
            text = form.comment_text.data,
            author_id=current_user.id,
            post_id=post_id
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('get_all_posts'))

    return render_template("post.html", post=requested_post, form=form, current_user=current_user,
                           current_year=date.today().year)


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user, current_year=date.today().year)


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@login_required  # it restrict user that are not login in to the website from access this function
@admin_only  # this allow only those assign as the admin to carry out the function we create the function at the top
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", form=form, current_year=date.today().year)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required  # it restrict user that are not login in to the website from access this function
@admin_only  # this allow only those assign as the admin to carry out the function we create the function at the top
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, current_year=date.today().year)


@app.route("/delete/<int:post_id>")
@login_required  # it restrict user that are not login in to the website from access this function
@admin_only  # this allow only those assign as the admin to carry out the function we create the function at the top
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
