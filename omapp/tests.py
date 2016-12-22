# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import contextlib
import json
try:
    from unittest import mock # py3.3+
except ImportError:
    import mock # < 3.3

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, modify_settings
import requests_mock
from rest_framework import status
from rest_framework.test import APIRequestFactory, APIClient

import settings
from . import models, tasks

SETTINGS = settings.Settings()


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
        self.instance = models.Instance.objects.create(
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
        execution = models.Execution.objects.get(id=data['id'])

        with self.settings(
                CELERY_ALWAYS_EAGER=True,
                CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                CELERY_BROKER_URL='memory://',
                BROKER_BACKEND='memory'):

            with requests_mock.Mocker() as m:
                m.get(SETTINGS.operation_registry_url + '/operations/42/', json={})
                # m.get('http://127.0.0.1:8000/operations/42/', json={})
                m.get(SETTINGS.resource_manager_url + '/clusters/', json=[
                  {
                    "id": 0,
                    "name": "string",
                    "uuid": "string",
                    "hints": "string",
                    "credential": "string",
                    "public_key": "string",
                    "status": "string",
                    "hosts_ids": [
                      "string"
                    ],
                    "targeted_slaves_count": 0,
                    "current_slaves_count": 0,
                    "hosts_ips": [
                      "string"
                    ],
                    "master_node_id": 0,
                    "master_node_ip": "string",
                    "user_id": 0,
                    "appliance": "string",
                    "appliance_impl": "string"
                  }
                ])
                tasks.process_execution_state(execution.id)

            self.assertEqual(execution.status, 'DEPLOYING')
