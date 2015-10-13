__author__ = 'leena'

from flask import Flask, jsonify, request
from celery import Celery
from config import library as settings, celerytest as celeryconfig


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

app = Flask(__name__, template_folder=settings.TEMPLATE_DIR)
app.config['CELERY_BROKER_URL'] = celeryconfig.BROKER_URL
app.config['CELERY_RESULT_BACKEND'] = celeryconfig.CELERY_RESULT_BACKEND
app.config['BROKER_TRANSPORT'] = celeryconfig.BROKER_TRANSPORT
app.config.update(CELERY_BROKER_URL='redis://localhost:6379',
                  CELERY_RESULT_BACKEND='redis://localhost:6379',
                  CELERY_IMPORTS=(app.import_name,))

async_celery = make_celery(app)


def mailer(data):
    from emailer import email_notifier
    print "Mailing: %s" % data
    category = data.get('category', None)
    author = data.get('author', None)
    sender = data.get('sender', None)
    subject = data.get('subject', None)
    recipient = data.get('recipient', None)
    email_content = data.get('email_content', None)
    email_notifier.delay(category, author, sender, recipient, subject,
                         email_content=email_content)


@app.route("/", methods=['POST'])
def index():
    mailer(request.json)
    return jsonify(dict(status='success'))


if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=True)
