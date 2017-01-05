# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import contextlib
import json
import random
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
from . import clients, models, tasks

SETTINGS = settings.Settings()


class AttrDict(dict):
    '''Because dictionaries are too good for Swagger clients'''
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def disable_remote_auth(test):
    test = modify_settings(MIDDLEWARE_CLASSES={
        'remove': [
            'common_dibbs.auth.auth.CentralAuthenticationMiddleware',
        ],
    })(test)
    return test


def op_id_get(**kwargs):
    '''https://dibbs-project.github.io/swagger-docs/or_api.html#!/Operations/get_operations_id'''
    return AttrDict({
        "id": kwargs.get('id', 0),
        "name": "string",
        "logo_url": "string",
        "author": 0,
        "description": "string",
        "string_parameters": "string",
        "file_parameters": "string",
        "implementations": [0]
    })


def opv_id_get(**kwargs):
    '''https://dibbs-project.github.io/swagger-docs/or_api.html#!/OperationVersions/get_operationversions_id'''
    return AttrDict({
        "id": kwargs.get('id', 0),
        "name": "string",
        "appliance": "string",
        "process_definition": 0,
        "cwd": "string",
        "script": "string",
        "output_type": "string",
        "output_parameters": "string"
    })


def clusters_get():
    return [
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
    ]


def clusters_post_factory(cid):
    def clusters_post(**kwargs):
        return AttrDict({
            "id": cid,
            "name": "string",
            "uuid": "string",
            "hints": "string",
            "credential": "string",
            "public_key": "string",
            "status": "string",
            "hosts_ids": ["string"],
            "targeted_slaves_count": 0,
            "current_slaves_count": 0,
            "hosts_ips": ["string"],
            "master_node_id": 0,
            "master_node_ip": "string",
            "user_id": 0,
            "appliance": "string",
            "appliance_impl": "string"
        })
    return clusters_post


def cid_get(**kwargs):
    return AttrDict({
        "id": kwargs.get('id', 0),
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
    })


class BasicTestCase(TestCase):

    @disable_remote_auth
    def test_root(self):
        """GET / : Sanity check; as basic as it gets."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class TestPatches(TestCase):
    def test_clusters_id_get(self):
        some_id = 1234
        with mock.patch(
            'omapp.clients.clusters.clusters_id_get',
            new=cid_get
        ):
            ret_id = clients.clusters.clusters_id_get(id=some_id).id

        self.assertEqual(some_id, ret_id)


    def test_clusters_post(self):
        some_id = 1234
        with mock.patch(
            'omapp.clients.clusters.clusters_id_get',
            new=cid_get
        ):
            ret_id = clients.clusters.clusters_id_get(id=some_id).id

        self.assertEqual(some_id, ret_id)


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

    # def tearDown(self):
    #     self.rfclient.logout()

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
                BROKER_BACKEND='memory'), \
                    mock.patch(
                        'omapp.clients.operations.operations_id_get',
                        new=op_id_get
                    ), \
                    mock.patch(
                        'omapp.clients.operation_versions.operationversions_id_get',
                        new=opv_id_get
                    ), \
                    mock.patch(
                        'omapp.clients.clusters.clusters_get',
                        new=clusters_get
                    ), \
                    mock.patch(
                        'omapp.clients.clusters.clusters_post',
                        new=clusters_post_factory(1234)
                    ) as clusterpost, \
                    mock.patch(
                        'omapp.clients.clusters.clusters_id_get',
                        new=cid_get
                    ):

            tasks.process_execution_state(execution.id)

            self.assertEqual(execution.cluster_id, 1234)
            self.assertEqual(execution.status, 'DEPLOYING')
            # assert clusterpost.called
