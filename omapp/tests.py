import contextlib

from django.test import TestCase, modify_settings
from django.conf import settings


class BasicTestCase(TestCase):

    @contextlib.contextmanager
    def disable_auth(self):
        with self.modify_settings(MIDDLEWARE_CLASSES={
            'remove': [
                'common_dibbs.auth.auth.CentralAuthenticationMiddleware',
            ],
        }):
            yield

    @disable_auth
    def test_root(self):
        """As basic as it gets."""
        with self.disable_auth():
            self.client.get('/')


class TasksTestCase(TestCase):

    def test_check_operations(self):
        pass
