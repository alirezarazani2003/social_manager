import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# بارگذاری تنظیمات از فایل settings.py با پیشوند CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# کشف خودکار task ها از اپ‌ها
app.autodiscover_tasks()
