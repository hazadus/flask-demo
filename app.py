from flask import Flask, render_template, flash, request, redirect, url_for
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.widgets import TextArea
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler(sys.stdout)  # output to file AND console
    ],
    format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
    datefmt='%d/%m/%Y %H:%M:%S',
    )

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = "my key for CSRF"  # TODO: exlude this from git!

# Init database
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Flask-login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Where to redirect if user is not logged in


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Create DB Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(32), nullable=False, unique=True)
    favorite_color = db.Column(db.String(16))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('Password is not a readable Attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Name %r>' % self.name


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    content = db.Column(db.Text)
    author = db.Column(db.String(128))
    slug = db.Column(db.String(256))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)


# Create Form Classes
class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = StringField('Content', validators=[DataRequired()], widget=TextArea())
    author = StringField('Author', validators=[DataRequired()])
    slug = StringField('Slug', validators=[DataRequired()])
    submit = SubmitField('Submit post')


class NamerForm(FlaskForm):
    name = StringField('Whatcha name', validators=[DataRequired()])
    submit = SubmitField('Submit')


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired()])
    favorite_color = StringField('Favorite Color')
    password_hash = PasswordField('Password', validators=[DataRequired(),
                                                          EqualTo('password_hash2',
                                                                  message='Passwords must match!')])
    password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash('Logged in successfully!')
                return redirect(url_for('dashboard'))
            else:
                flash('Wrong password, try again!')
        else:
            flash('Wrong username, try again!')

    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required  # Redirect to Login page if user is not logged in
def dashboard() -> str:
    return render_template('dashboard.html')


@app.route('/user/<user_name>')
def view_user(user_name):  # TODO: remove from project? It's useless now.
    return render_template('user.html', user_name=user_name)


@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name_ = email = None
    form = UserForm()

    if form.validate_on_submit():
        user_ = Users.query.filter_by(email=form.email.data).first()  # Check if this email is already in DB
        if user_ is None:
            hashed_password = generate_password_hash(form.password_hash.data, 'sha256')
            user_ = Users(username=form.username.data,
                          name=form.name.data,
                          email=form.email.data,
                          favorite_color=form.favorite_color.data,
                          password_hash=hashed_password)
            db.session.add(user_)
            db.session.commit()
        name_ = form.name.data
        # Clear out the form
        form.username.data = ''
        form.name.data = ''
        form.email.data = ''
        form.favorite_color.data = ''
        form.password_hash.data = ''
        form.password_hash2.data = ''
        flash('New user added successfully!')

    our_users = Users.query.order_by(Users.date_added)
    return render_template('add_user.html',
                           name=name_,
                           email=email,
                           form=form,
                           our_users=our_users)


# Update User Record in DB
@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update(user_id):  # TODO: rename to 'update_user'
    form = UserForm()
    name_to_update = Users.query.get_or_404(user_id)

    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        # noinspection PyBroadException
        try:
            db.session.commit()
            flash('User updated successfully!')
            return render_template('update.html',
                                   form=form,
                                   name_to_update=name_to_update)
        except:
            flash('Error! Looks like there was a problem, please try again.')
            return render_template('update.html',
                                   form=form,
                                   name_to_update=name_to_update)
    else:
        return render_template('update.html',
                               form=form,
                               name_to_update=name_to_update)


@app.route('/delete/<int:user_id>')
def delete(user_id):  # TODO: rename to 'delete_user'
    name_ = email = None
    form = UserForm()
    user_to_delete = Users.query.get_or_404(user_id)
    our_users = Users.query.order_by(Users.date_added)

    # noinspection PyBroadException
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('User deleted successfully.')

        return render_template('add_user.html',
                               name=name_,
                               email=email,
                               form=form,
                               our_users=our_users)
    except:
        flash('There was a problem deleting user, please try again!')
        return render_template('add_user.html',
                               name=name_,
                               email=email,
                               form=form,
                               our_users=our_users)


@app.route('/name', methods=['GET', 'POST'])
def name():  # TODO: remove?
    name_ = None
    form = NamerForm()

    # Validate form
    if form.validate_on_submit():
        name_ = form.name.data
        form.name.data = ''
        flash('Form successfully submitted.')

    return render_template('name.html',
                           name=name_,
                           form=form)


@app.route('/add-post', methods=['GET', 'POST'])
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        post_ = Posts(title=form.title.data, content=form.content.data, author=form.author.data, slug=form.slug.data)

        # Clear the form
        form.title.data = ''
        form.content.data = ''
        form.author.data = ''
        form.slug.data = ''

        # Add post to DB
        db.session.add(post_)
        db.session.commit()

        flash('Blog post submitted successfully!')

    return render_template('add_post.html', form=form)


@app.route('/posts')
def posts():  # TODO: rename to say 'view_all_posts'?
    posts_ = Posts.query.order_by(Posts.date_posted)
    return render_template('posts.html', posts=posts_)


@app.route('/posts/<int:post_id>')
def view_post(post_id):
    post_ = Posts.query.get_or_404(post_id)
    return render_template('post.html', post=post_)


@app.route('/posts/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post_ = Posts.query.get_or_404(post_id)
    form = PostForm()

    # If post was actually edited already:
    if form.validate_on_submit():
        post_.title = form.title.data
        post_.author = form.author.data
        post_.content = form.content.data
        post_.slug = form.slug.data
        # Update DB
        db.session.add(post_)  # Update DB with changed post
        db.session.commit()
        flash('Post has been updated successfully!')
        return redirect(url_for('view_post', post_id=post_.id))

    # Pass data to fill out the form for editing
    form.title.data = post_.title
    form.author.data = post_.author
    form.slug.data = post_.slug
    form.content.data = post_.content
    return render_template('edit_post.html', form=form)


@app.route('/posts/delete/<int:post_id>')
def delete_post(post_id):
    post_to_delete = Posts.query.get_or_404(post_id)

    # noinspection PyBroadException
    try:
        db.session.delete(post_to_delete)
        db.session.commit()
        flash("Blog post was successfully deleted.")
        posts_ = Posts.query.order_by(Posts.date_posted)
        return render_template('posts.html', posts=posts_)
    except:
        flash("There was a problem deleting blog post. Please try again!")
        posts_ = Posts.query.order_by(Posts.date_posted)
        return render_template('posts.html', posts=posts_)


@app.route('/date')
def get_current_date():
    return {"Date": date.today()}


# Create custom Error Pages
# Invalid IRL
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run()
