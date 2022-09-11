# flask-demo
Basic web blog intended to try out Flask capatibilities..

## Dependencies
- `flask`
- `flask-wtf`
- `flask-sqlalchemy`
- `flask-login`
- `flask-ckeditor`
- `sentry-sdk[flask]`
- Optional: `Flask-Migrate`
- Optional: `gunicorn`

## References
- [CodeMy Flask Fridays YoutTube playlist](https://www.youtube.com/watch?v=0Qxtt4veJIc&list=PLCC34OHNcOtolz2Vd9ZSeSXWc8Bq23yEz&index=2)
- [Flask Documentation](https://flask.palletsprojects.com/en/2.2.x/#)
- - [Flask: Message Flashing](https://flask.palletsprojects.com/en/2.2.x/patterns/flashing/?highlight=flash)
- [Bootstrap Documentation](https://getbootstrap.com/docs/5.2/getting-started/introduction/)
- [Bootstrap Cheatsheet](https://getbootstrap.com/docs/5.2/examples/cheatsheet/)
- - [Bootstrap: Navbar](https://getbootstrap.com/docs/5.2/components/navbar/#how-it-works)
- - [Bootstrap: Form Controls](https://getbootstrap.com/docs/5.2/forms/form-control/)
- - [Bootstrap: Buttons](https://getbootstrap.com/docs/5.2/components/buttons/)
- - [Bootstrap: Alerts](https://getbootstrap.com/docs/5.2/components/alerts/)
- - [Bootstrap: Shadows](https://getbootstrap.com/docs/5.2/utilities/shadows/)
- - [Bootstrap: Tables](https://getbootstrap.com/docs/5.2/content/tables/)
- [WTForms Documentation](https://wtforms.readthedocs.io/en/3.0.x/)
- [SQLAlchemy](https://www.sqlalchemy.org)
- [Sentry.io Flask Integration](https://docs.sentry.io/platforms/python/guides/flask/)
- [Flask-login Documentation](https://flask-login.readthedocs.io/en/latest/)
- [Flask-CKEditor Documentation](https://flask-ckeditor.readthedocs.io/en/latest/)
- [Gunicorn Docs](https://gunicorn.org/#deployment)

## Notes
- Install Sentry:
- - `pip install --upgrade 'sentry-sdk[flask]'`
- To run in development mode:
- - `export FLASK_ENV=development`
- - `flask run`
- We can use `flask shell` for debug purposes ([see example here](https://youtu.be/8ebIEefhBpM?t=599)).
- To run on server:
- - `cd /usr/projects/flask-demo`
- - `git pull` if you need to update the code
- - `source bin/activate`
- - `gunicorn app:app -b localhost:8000 &` (see link 1 below for details)
- - [1. Deploy flask app with nginx using gunicorn and supervisor](https://medium.com/ymedialabs-innovation/deploy-flask-app-with-nginx-using-gunicorn-and-supervisor-d7a93aa07c18)
- - [2. Deploying Flask Application on VPS Linux Server using Nginx](https://medium.com/geekculture/deploying-flask-application-on-vps-linux-server-using-nginx-a1c4f8ff0010)
- - List gunicorn processess: `ps ax | grep gunicorn`
- - Kill process: `kill -9 PID`
- [CodeMy Flask Fridays #9: How to use MySQL instead of sqlite](https://youtu.be/hQl2wyJvK5k)
- Copy DB to server: `scp /Users/hazadus/PycharmProjects/flask-demo/blog_data.db root@188.225.72.155:/usr/projects/flask-demo`

## Deploying on Linux with nginx and gunicorn
Create virtualenv, clone repo from github, then:
```
$ pip3 install Flask
$ pip3 install -r requirements.txt
```
Run app with gunicorn:
```
$ pip3 install gunicorn
$ gunicorn app:app -b localhost:8000 &
```
Setup ngingx:
```
$ sudo vim /etc/nginx/conf.d/virtual.conf
```
Edit nginx config:
```
server {
    listen       80;
    server_name  your_public_dnsname_here;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```
Proxy pass directive must be the same port on which the gunicorn process is listening.
Restart the nginx web server.
```
$ sudo nginx -t
$ sudo service nginx restart
```

## Working with database
Initializing database after installation:
```python
from app import db
db.create_all()
```
Then, create admin user ([more in docs](https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/)):
```python
from app import Users
from werkzeug.security import generate_password_hash
password_hash = generate_password_hash('12345678', 'sha256')
admin = Users(username='hazadus', name='Alexander Goldovsky', email='hazadus7@gmail.com', is_admin=True, password_hash=password_hash)
db.session.add(admin)
db.session.commit()
```
After adding a new column to existing DB table, we need to do the "migrate" thing. To do so, in terminal (in venv, of course):
```
flask db init
flask db stamp head
flask db migrate -m 'Initial migration'
flask db upgrade
```