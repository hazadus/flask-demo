# flask-demo
Basic website intended to try out Flask capatibilities..

## Dependencies
- `flask`
- `flask-wtf`
- `flask-sqlalchemy`
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
- [Gunicorn Docs](https://gunicorn.org/#deployment)

## Notes
- To run in development mode:
- - `export FLASK_ENV=development`
- - `flask run`
- To run on server:
- - `gunicorn app:app -b localhost:8000 &` (see link 1 below for details)
- - [1. Deploy flask app with nginx using gunicorn and supervisor](https://medium.com/ymedialabs-innovation/deploy-flask-app-with-nginx-using-gunicorn-and-supervisor-d7a93aa07c18)
- - [2. Deploying Flask Application on VPS Linux Server using Nginx](https://medium.com/geekculture/deploying-flask-application-on-vps-linux-server-using-nginx-a1c4f8ff0010)
- - List gunicorn processess: `ps ax | grep gunicorn`
- - Kill process: `kill -9 PID`
- To create new sqlite DB, via Python terminal:
- - `from app import db`
- - `db.create_all()`
- [CodeMy Flask Fridays #9: How to use MySQL instead of sqlite](https://youtu.be/hQl2wyJvK5k)
- After adding a new column to existing DB table, we need to do the "migrate" thing. To do so, in terminal (in venv, of course):
- - `flask db init`
- - `flask db migrate -m 'Initial migration'`
- - `flask db upgrade`