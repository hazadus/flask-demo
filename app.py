"""
Flask Web Blog template

Written by Hazadus for test and learning purposes.
Please visit https://www.hazadus.ru for more info.
"""

import uuid as uuid
import logging
import sys
import os

from flask import Flask, render_template, flash, request, redirect, url_for, abort
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_ckeditor import CKEditor
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, EqualTo
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from feedwerk.atom import AtomFeed
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Configure logger
logging.basicConfig(level=logging.INFO,
                    handlers=[
                        logging.FileHandler("log.txt"),
                        logging.StreamHandler(sys.stdout)  # output to file AND console
                    ],
                    format="%(asctime)s | %(levelname)s | %(module)s / %(funcName)s: %(lineno)d - %(message)s",
                    datefmt='%d/%m/%Y %H:%M:%S',
                    )

# Configure Sentry, if not in development mode
if os.getenv('FLASK_DEBUG') != '1':
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            FlaskIntegration(),
        ],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0

        # By default the SDK will try to use the SENTRY_RELEASE
        # environment variable, or infer a git commit
        # SHA as release, however you may want to set
        # something more human-readable.
        # release="myapp@1.0.0",
    )
    logging.info('Sentry activated.')

# Configure Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_CSRF')
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # TODO: convert to os.path.join, then test profile pic uploading
app.config['CKEDITOR_ENABLE_CODESNIPPET'] = True

# Init database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Flask-login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Where to redirect if user is not logged in

ckeditor = CKEditor(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Create DB Model
class Users(db.Model, UserMixin):
    """Users DB table model."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(32), nullable=False, unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    favorite_color = db.Column(db.String(16))
    profile_pic = db.Column(db.String(), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.now())
    password_hash = db.Column(db.String(128))
    # User can have many posts
    posts = db.relationship('Posts', backref='author')  # Usage from Jinja: {{ post.author.name }}

    @property
    def password(self):
        raise AttributeError('Password is not a readable Attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name}>'


class Tags(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))

    def __repr__(self):
        return f'<Tag "{self.name}">'


post_tag = db.Table('post_tag',
                    db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
                    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
                    )


class Posts(db.Model):
    """Blog post DB table model"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    summary = db.Column(db.Text, default=None)
    content = db.Column(db.Text)
    banner_pic = db.Column(db.String(), nullable=True)
    slug = db.Column(db.String(256))
    date_posted = db.Column(db.DateTime, default=datetime.now())
    is_draft = db.Column(db.Boolean, default=False)
    views_count = db.Column(db.Integer, default=0)
    # Foreign key to link users (refer to primary key of the user), and tags
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tags = db.relationship('Tags', secondary=post_tag, backref='posts')

    def __repr__(self):
        return f'<Post "{self.title}">'


class SearchForm(FlaskForm):
    search_query = StringField('Search query', validators=[DataRequired()])
    submit = SubmitField('Submit')


# Create Form Classes
class PostForm(FlaskForm):
    """Used to create new blog post, or edit existing."""
    title = StringField('Title', validators=[DataRequired()])
    slug = StringField('Slug', validators=[DataRequired()])
    summary = StringField('Summary', validators=[DataRequired()])  # TODO: change to larger text field
    banner_pic = StringField('Picture filename')  # Assuming the file in 'uploads' folder
    content = CKEditorField('Body', validators=[DataRequired()])
    is_draft = BooleanField('Mark as Draft')
    is_date_posted_to_current = BooleanField('Set \'posted date\' to current')
    submit = SubmitField('Submit post')


class UserForm(FlaskForm):
    """Used to sign up a new user, or edit an existing one."""
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired()])
    favorite_color = StringField('Favorite Color')
    password_hash = PasswordField('Password', validators=[DataRequired(),
                                                          EqualTo('password_hash2',
                                                                  message='Passwords must match!')])
    password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
    profile_pic = FileField('Profile Picture')
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')


# Pass stuff to Navbar
@app.context_processor
def base():
    # This is to pass search form into navbar
    form = SearchForm()
    return dict(form=form)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/debug-sentry')
@login_required
def trigger_error():
    return 1 / 0


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


@app.route('/search', methods=['POST'])
def search():  # TODO: validate data required
    form = SearchForm()
    if form.validate_on_submit():
        search_results = Posts.query.filter(Posts.content.like('%' + form.search_query.data + '%'))
        search_results = search_results.filter(Posts.is_draft.is_(False))  # Remove drafts from search results
        search_results = search_results.order_by(Posts.title).all()
        return render_template('search.html', form=form,
                               search_query=form.search_query.data,
                               search_results=search_results)
    else:
        return redirect(url_for('index'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required  # Redirect to Login page if user is not logged in
def dashboard() -> str:
    return render_template('dash_user.html')


@app.route('/dashboard/user', methods=['GET', 'POST'])
@login_required
def dashboard_user() -> str:
    # TODO: move update profile stuff here.
    # Video #25: https://www.youtube.com/watch?v=o6YjyOt2Zhc
    return render_template('dash_user.html')


@app.route('/dashboard/posts', methods=['GET', 'POST'])
@login_required
def dashboard_posts() -> str:
    posts = Posts.query.filter(db.and_(Posts.author_id == current_user.id,
                                       Posts.is_draft == False)).order_by(Posts.date_posted.desc())
    return render_template('dash_posts.html', posts=posts)


@app.route('/dashboard/drafts', methods=['GET', 'POST'])
@login_required
def dashboard_drafts() -> str:
    posts = Posts.query.filter(db.and_(Posts.author_id == current_user.id,
                                       Posts.is_draft == True)).order_by(Posts.date_posted.desc())
    return render_template('dash_drafts.html', posts=posts)


@app.route('/dashboard/users', methods=['GET', 'POST'])
@login_required
def dashboard_users() -> str:
    if not current_user.is_admin:
        abort(404)

    all_users = Users.query.order_by(Users.date_added).all()
    return render_template('dash_users.html', all_users=all_users)


@app.route('/dashboard/uploads', methods=['GET', 'POST'])
@login_required
def dashboard_uploads() -> str:
    if not current_user.is_admin:
        abort(404)

    uploads_dir = os.path.abspath(os.path.join('static', 'uploads'))
    uploads = [[file, os.stat(os.path.join(uploads_dir, file)).st_size]
               for file in os.listdir(uploads_dir)]
    uploads.sort()
    return render_template('dash_uploads.html', uploads=uploads)


@app.route('/user/add', methods=['GET', 'POST'])
def add_user() -> str:
    name = email = None
    form = UserForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()  # Check if this email is already in DB
        if user is None:
            hashed_password = generate_password_hash(form.password_hash.data, 'sha256')
            user = Users(username=form.username.data,
                         name=form.name.data,
                         email=form.email.data,
                         favorite_color=form.favorite_color.data,
                         password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        # Clear out the form
        form.username.data = ''
        form.name.data = ''
        form.email.data = ''
        form.favorite_color.data = ''
        form.password_hash.data = ''
        form.password_hash2.data = ''
        flash('New user added successfully!')

    return render_template('add_user.html',
                           name=name,
                           email=email,
                           form=form)


@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
@login_required  # Redirect to Login page if user is not logged in
def update_user(user_id: int) -> str:
    """Update user record in DB after editing."""
    form = UserForm()
    user_to_update = Users.query.get_or_404(user_id)

    if request.method == 'POST':  # TODO: add check if it is correct user posting, or an admin
        user_to_update.name = request.form['name']
        user_to_update.email = request.form['email']
        user_to_update.favorite_color = request.form['favorite_color']

        if request.files['profile_pic']:
            profile_pic_filename = str(uuid.uuid1()) + '_' + secure_filename(request.files['profile_pic'].filename)
            user_to_update.profile_pic = profile_pic_filename
            request.files['profile_pic'].save(os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename))
            # TODO: delete old profile pic after uploading new

        # noinspection PyBroadException
        try:
            db.session.commit()
            flash('User updated successfully!')
            return render_template('update_user.html',
                                   form=form,
                                   user_to_update=user_to_update)
        except:
            flash('Error! Looks like there was a problem, please try again.')
            return render_template('update_user.html',
                                   form=form,
                                   user_to_update=user_to_update)
    else:
        return render_template('update_user.html',
                               form=form,
                               user_to_update=user_to_update)


@app.route('/delete/<int:user_id>')
@login_required  # Redirect to Login page if user is not logged in
def delete_user(user_id: int) -> str:
    user_to_delete = Users.query.get_or_404(user_id)
    all_users = Users.query.order_by(Users.date_added)

    if current_user.is_admin:
        # noinspection PyBroadException
        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('User deleted successfully.')

            return render_template('dash_users.html', all_users=all_users)
        except:
            flash('There was a problem deleting user, please try again!')
            return render_template('dash_users.html', all_users=all_users)
    else:
        flash('Only admins can delete user accounts!')
        return render_template('dashboard.html')


@app.route('/add-post', methods=['GET', 'POST'])
@login_required  # Redirect to Login page if user is not logged in
def add_post() -> str:
    """Show or process 'Add post' page."""
    form = PostForm()

    if form.validate_on_submit():
        post = Posts(title=form.title.data,
                     content=form.content.data,
                     summary=form.summary.data,
                     banner_pic=form.banner_pic.data,
                     author_id=current_user.id,  # make relationship with currently logged in user as author
                     is_draft=form.is_draft.data,
                     slug=form.slug.data)

        # Clear the form
        form.title.data = ''
        form.slug.data = ''
        form.summary.data = ''
        form.banner_pic.data = ''
        form.content.data = ''
        form.is_draft.data = False

        # Add post to DB
        db.session.add(post)
        db.session.commit()

        flash('Blog post submitted successfully!')

    return render_template('add_post.html', form=form)


@app.route('/posts')
def view_all_posts() -> str:
    """Show 'All posts' section."""
    posts = Posts.query.filter_by(is_draft=False)
    posts = posts.order_by(Posts.date_posted.desc())
    tags = Tags.query.order_by(Tags.name)
    return render_template('posts.html', posts=posts, tags=tags)


@app.route('/post/<int:post_id>')
def view_post(post_id: int):
    post = Posts.query.get_or_404(post_id)
    return redirect(url_for('view_post_by_slug', post_slug=post.slug))


@app.route('/post/<string:post_slug>')
def view_post_by_slug(post_slug: str) -> str:
    post = Posts.query.filter(Posts.slug == post_slug).first_or_404()
    # if post.is_draft:  # TODO: make admin or post author able to view drafts
    #     abort(404)
    similar_posts = Posts.query.join(Tags.posts).filter \
        (Tags.id.in_(tag.id for tag in post.tags)).filter(Posts.id != post.id).all()
    tags = Tags.query.order_by(Tags.name)
    most_viewed_posts = Posts.query.order_by(Posts.views_count.desc()).limit(3).all()

    if not post.is_draft:
        post.views_count += 1
        db.session.add(post)  # Update DB with changed post
        db.session.commit()
    return render_template('post.html',
                           post=post,
                           similar_posts=similar_posts,
                           tags=tags,
                           most_viewed_posts=most_viewed_posts)


@app.route('/posts/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required  # Redirect to Login page if user is not logged in
def edit_post(post_id: int):
    post = Posts.query.get_or_404(post_id)
    form = PostForm()

    if post.author.id == current_user.id or current_user.is_admin:
        # If post was actually edited already:
        if form.validate_on_submit():
            post.title = form.title.data
            post.slug = form.slug.data
            post.summary = form.summary.data
            post.banner_pic = form.banner_pic.data
            post.content = form.content.data
            post.is_draft = form.is_draft.data

            if form.is_date_posted_to_current.data:
                post.date_posted = datetime.now()

            # Update DB
            db.session.add(post)  # Update DB with changed post
            db.session.commit()
            flash('Post has been updated successfully!')
            return redirect(url_for('view_post', post_id=post.id))

        # Pass data to fill out the form for editing
        form.title.data = post.title
        form.slug.data = post.slug
        form.summary.data = post.summary
        form.banner_pic.data = post.banner_pic
        form.content.data = post.content
        form.is_draft.data = post.is_draft
        form.is_date_posted_to_current.data = False
        return render_template('edit_post.html', form=form)
    else:
        flash("Can't edit other user's posts, sorry.")
        return redirect(url_for('view_post', post_id=post.id))


@app.route('/posts/delete/<int:post_id>')
@login_required  # Redirect to Login page if user is not logged in
def delete_post(post_id: int) -> str:
    post_to_delete = Posts.query.get_or_404(post_id)

    if post_to_delete.author.id == current_user.id or current_user.is_admin:
        # noinspection PyBroadException
        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            flash("Blog post was successfully deleted.")
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template('posts.html', posts=posts)
        except:
            flash("There was a problem deleting blog post. Please try again!")
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template('posts.html', posts=posts)
    else:
        flash("Can't delete other user's post.")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template('posts.html', posts=posts)


@app.route('/posts/tag/<string:tag_name>')
def view_tag_posts(tag_name: str) -> str:
    tag = Tags.query.filter(Tags.name == tag_name).first()

    if not tag:
        abort(404)

    posts = Posts.query.filter(Posts.tags.contains(tag))
    return render_template('tag_posts.html', tag=tag, posts=posts)


@app.route('/rss/')
def rss():
    feed = AtomFeed(title='New Posts from hazadus.ru',
                    feed_url='https://www.hazadus.ru/rss/', url='https://www.hazadus.ru/')
    posts = Posts.query.filter_by(is_draft=False)
    posts = posts.order_by(Posts.date_posted.desc())

    for post in posts:
        feed.add(post.title,
                 post.summary,  # post.content,
                 content_type='html',
                 author=post.author.username,
                 url='https://www.hazadus.ru' + url_for('view_post_by_slug', post_slug=post.slug),
                 updated=post.date_posted,
                 published=post.date_posted)

    return feed.get_response()


@app.route('/date')
def get_current_date() -> dict:
    """Sample JSON API implementation for test purposes."""
    return {"Date": date.today()}


# Create custom Error Pages
# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run()
