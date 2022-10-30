from flask import Flask
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
# routes imports
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, UserMixin, logout_user, login_required
from flask import (render_template, url_for, 
    redirect, request, abort)
from flask_login import current_user

import os
from dotenv import load_dotenv

load_dotenv()

base_dir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///' + os.path.join(base_dir,'blog.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))


@app.route("/home")
@app.route("/")
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)

@app.route("/contact")
def contact():
    return render_template('contact.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    username_error = None
    email_error = None
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm')
        user_name = User.query.filter_by(username=username).first()
        user_email = User.query.filter_by(email=email).first()
        if user_name:
            username_error = 'username already exists!'

        elif user_email:
            email_error = 'email already exists!'
        else:
            password_hash = generate_password_hash(password)
            if check_password_hash(password_hash, confirm_password):
                new_user = User(username=username, email=email, password=password_hash)
                db.session.add(new_user)
                db.session.commit()

                return redirect(url_for('login'))

    return render_template('register.html', errors={
            'username':username_error,
            'email' : email_error
        })

@app.route("/about", methods=['GET', 'POST'])
@login_required
def about():
    current_username = current_user.username
    current_email = current_user.email
    username_error = None
    email_error = None
    posts = Post.query.filter_by(author=current_user)
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        user_name = User.query.filter_by(username=username).first()
        user_email = User.query.filter_by(email=email).first()
        if user_name and user_name.username != current_username:
            username_error = 'username already exists!'
        elif user_email and user_email.email != current_email:
            email_error = 'email already exists!'
        else:
            current_user.username = username
            current_user.email = email
            db.session.commit()
            return redirect(url_for('about'))

    return render_template('about.html', title='account',
        username=current_username, email=current_email, posts=posts,
        errors={
            'username':username_error,
            'email' : email_error
        })


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        post = Post(title=title, content=content, author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', legend="Create Post", 
        btn="Post", action=url_for('new_post'))

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        post.title = title
        post.content = content
        db.session.commit()
        return redirect(url_for('post', post_id=post.id))
    return render_template('create_post.html', legend="Update Post",
        title="Edit Post", post=post, btn="Update Post", action=url_for('update_post', post_id=post.id))

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))




if __name__=="__main__":
    app.run(debug=True)