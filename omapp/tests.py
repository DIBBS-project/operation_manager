# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import contextlib
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, modify_settings
from rest_framework import status
from rest_framework.test import APIRequestFactory, APIClient

from .models import Instance

def disable_remote_auth(test):
    test = modify_settings(MIDDLEWARE_CLASSES={
        'remove': [
            'common_dibbs.auth.auth.CentralAuthenticationMiddleware',
        ],
    })(test)
    return test


class BasicTestCase(TestCase):

    @disable_remote_auth
    def test_root(self):
        """GET / : Sanity check; as basic as it gets."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class ExecutionsTestCase(TestCase):

    def setUp(self):
        # self.factory = APIRequestFactory()
        username = 'coffee'
        password = 'caffeine'
        self.user = User.objects.create_superuser(
            username,
            '{}@example.com'.format(username),
            password,
        )

        self.rfclient = APIClient()
        self.rfclient.force_authenticate(user=self.user)

        # make some dummy instance
        self.instance = Instance.objects.create(
            author=self.user,
            name='test_instance',
            process_definition_id=42, #?
        )

    def tearDown(self):
        self.rfclient.logout()

    @disable_remote_auth
    def test_api_creation(self):
        request_data = {
            'operation_instance': self.instance.pk,
            'resource_provisioner_token': 'token',
            'callback_url': 'callback_url',
            'slave_nodes_count': 0,
        }

        response = self.rfclient.post(
            '/executions/',
            request_data,
            format="json",
        )
        data = json.loads(response.content.decode(response.charset))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # def test_state_transitions(self):
        # split this up later...
        # data
