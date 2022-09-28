#!/bin/bash
# chmod a+x ./run_app.sh

export FLASK_ENV=development

# Set these env vars accroding to yours
export SENTRY_DSN=SentryToken
export FLASK_CSRF=SecretKey

cd /usr/projects/flask-demo
source bin/activate
gunicorn app:app -b localhost:8000 &

# flask run