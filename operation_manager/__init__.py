# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ['process_dispatcher']
