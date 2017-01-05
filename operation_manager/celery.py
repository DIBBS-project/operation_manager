# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

from omapp.tasks import check_operations_periodically

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'operation_manager.settings')

app = Celery('operation_manager')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, periodic_task.s(), name='add every 10')


@app.task(bind=True)
def periodic_task(self):
    print("Calling check_operations_periodically task")
    check_operations_periodically()
