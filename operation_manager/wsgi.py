"""
WSGI config for operation_manager project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "operation_manager.settings")

application = get_wsgi_application()

# Create the process in charge of processing executions FSM
from omapp.periodictasks import create_periodic_check_thread
create_periodic_check_thread()
