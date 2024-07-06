import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mailer.settings")
app = Celery("mailer")
app.config_from_object("django.conf:settings", namespace="CELERY")


@app.task(bind=True)
def shared_tasks():
    return


app.autodiscover_tasks()
