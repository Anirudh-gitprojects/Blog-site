from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm
from flask_gravatar import Gravatar
login_manager = LoginManager()
from flask import abort,wrappers
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import hashlib

Base = declarative_base()
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager.init_app(app)
##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from flask_gravatar import Gravatar
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
##CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments=relationship("Comment",back_populates="parent_posts")


class User(UserMixin,db.Model):
    __tablename__= "users"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(250),nullable=False)
    email=db.Column(db.String(250),nullable=False)
    password=db.Column(db.String(250),nullable=False)
    comment=relationship("Comment",back_populates="comment_author")
    posts = relationship("BlogPost", back_populates="author")


class Comment(db.Model):
    __tablename__="comments"
    id=db.Column(db.Integer,primary_key=True)
    author_id=Column(db.Integer,db.ForeignKey("users.id"))
    comment_author=relationship("User",back_populates="comment")
    post_id=db.Column(db.Integer,db.ForeignKey("blog_posts.id"))
    parent_posts=relationship("BlogPost",back_populates="comments")
    text=db.Column(db.Text,nullable=False)

db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    for p in posts:
        print(p.author.name)
    return render_template("index.html", all_posts=posts)


@app.route('/register',methods=['POST','GET'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        user_name=form.name.data
        user_email=form.email.data
        user_pass=form.password.data
        query_email=db.session.query(User).filter_by(email=user_email).first()
        if query_email:
            flash('You already have an account under the email address. Log In!')
            return redirect(url_for('login'))
        else:
            hashed_pass=generate_password_hash(user_pass,method='pbkdf2:sha256', salt_length=8)
            new_user=User(name=user_name,email=user_email,password=hashed_pass)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html",form=form)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id==1:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function

@app.route('/del/<var>')
def del_comment(var):
    return render_template("post.html")

def calculateemail_hash(email_):
    email_=str(email_.strip().lower())
    hashpass = hashlib.md5(email_.encode('utf8')).hexdigest()
    return hashpass

@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=db.session.query(User).filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash('Incorrect password')
                return redirect(url_for('login'))
        else:
            flash('Email does not exist,please try again.')
            return redirect(url_for('login'))
    return render_template("login.html",form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['POST','GET'])
def show_post(post_id):
    form=CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if form.validate_on_submit():
        if not  current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))
        else:
            comment_result=form.comment.data
            new_comment = Comment(
                text=comment_result,
                comment_author=current_user,
                parent_posts=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
    return render_template("post.html", post=requested_post,form=form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post",methods=['POST','GET'])
@login_required
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
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>",methods=['POST','GET'])
@admin_required
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
