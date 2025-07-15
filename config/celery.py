# social_manager/celery.py
import os
from celery import Celery
from utils.loging_setup import setup_logging

setup_logging()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
