from flask import Flask, render_template, flash, request
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = "my key for CSRF"  # TODO: exlude this from git!
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Create DB Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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


# Create Form Classes
class NamerForm(FlaskForm):
    name = StringField('Whatcha name', validators=[DataRequired()])
    submit = SubmitField('Submit')


class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired()])
    favorite_color = StringField('Favorite Color')
    password_hash = PasswordField('Password', validators=[DataRequired(),
                                                          EqualTo('password_hash2',
                                                                  message='Passwords must match!')])
    password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', user_name=name)


@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = email = None
    form = UserForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()  # Check if this email is already in DB
        if user is None:
            hashed_password = generate_password_hash(form.password_hash.data, 'sha256')
            user = Users(name=form.name.data, email=form.email.data, favorite_color=form.favorite_color.data,
                         password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.email.data = ''
        form.favorite_color.data = ''
        form.password_hash.data = ''
        form.password_hash2.data = ''
        flash('New user added successfully!')

    our_users = Users.query.order_by(Users.date_added)
    return render_template('add_user.html',
                           name=name,
                           email=email,
                           form=form,
                           our_users=our_users)


# Update User Record in DB
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)

    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
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


@app.route('/delete/<int:id>')
def delete(id):
    name = email = None
    form = UserForm()
    user_to_delete = Users.query.get_or_404(id)
    our_users = Users.query.order_by(Users.date_added)

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('User deleted successfully.')

        return render_template('add_user.html',
                               name=name,
                               email=email,
                               form=form,
                               our_users=our_users)
    except:
        flash('There was a problem deleting user, please try again!')
        return render_template('add_user.html',
                               name=name,
                               email=email,
                               form=form,
                               our_users=our_users)


@app.route('/name', methods=['GET', 'POST'])
def name():
    name = None
    form = NamerForm()

    # Validate form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash('Form successfully submitted.')

    return render_template('name.html',
                           name=name,
                           form=form)


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
