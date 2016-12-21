import contextlib

from django.test import TestCase, modify_settings
from django.conf import settings


def disable_auth(test):
    test = modify_settings(MIDDLEWARE_CLASSES={
        'remove': [
            'common_dibbs.auth.auth.CentralAuthenticationMiddleware',
        ],
    })(test)
    return test


class BasicTestCase(TestCase):

    @disable_auth
    def test_root(self):
        """As basic as it gets."""
        self.client.get('/')


class TasksTestCase(TestCase):

    def _test_check_operations(self):
        pass
