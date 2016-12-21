# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import contextlib

from django.conf import settings
from django.test import TestCase, modify_settings


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
