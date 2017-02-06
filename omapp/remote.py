# coding: utf-8
'''
Clients. They don't need any reconfiguring (apart from maybe the agent
clients?), so just one & done 'em.
'''
from __future__ import absolute_import, print_function

import logging

from django.conf import settings

from common_dibbs.django import obo_headers
from common_dibbs.clients.ar_client.apis import ApplianceImplementationsApi
from common_dibbs.clients.or_client.apis import (OperationsApi,
                                                 OperationVersionsApi)
from common_dibbs.clients.rm_client.apis import (ClusterDefinitionsApi,
                                                 CredentialsApi,
                                                 HostDefinitionsApi)
from common_dibbs.clients.rm_client.rest import ApiException as RmApiException
from common_dibbs.django import get_request, relay_swagger

from common_dibbs.clients import ApiException


logger = logging.getLogger(__name__)


def _attach_auth_header(client, obo_user=None):
    try:
        request = get_request() # global request object (thread-local)
    except AttributeError:
        if obo_user is None:
            raise ValueError('no user specified and cannot access global request')

        headers = obo_headers(obo_user)
        logger.info('constructed token on behalf of user "{}" -> "{}"'.format(
            obo_user, headers))
        client.api_client.default_headers.update(headers)
    else:
        relay_swagger(client, request)


def appliances_impl_name_get(name, obo_user=None):
    # request = get_request()

    appliance_implementations = ApplianceImplementationsApi()
    appliance_implementations.api_client.host = settings.DIBBS['urls']['ar']
    # relay_swagger(appliance_implementations, request)
    _attach_auth_header(appliance_implementations, obo_user)

    return appliance_implementations.appliances_impl_name_get(name)


def clusters_get(obo_user=None):
    clusters = ClusterDefinitionsApi()
    clusters.api_client.host = settings.DIBBS['urls']['rm']
    _attach_auth_header(clusters, obo_user)

    return clusters.clusters_get()


def clusters_post(data, obo_user=None):
    # request = get_request()

    clusters = ClusterDefinitionsApi()
    clusters.api_client.host = settings.DIBBS['urls']['rm']
    # relay_swagger(clusters, request)
    _attach_auth_header(clusters, obo_user)

    return clusters.clusters_post(data=data)


def clusters_id_get(id, obo_user=None):
    # request = get_request()

    clusters = ClusterDefinitionsApi()
    clusters.api_client.host = settings.DIBBS['urls']['rm']
    # relay_swagger(clusters, request)
    _attach_auth_header(clusters, obo_user)

    return clusters.clusters_id_get(id=id)


def clusters_id_new_account_post(id, obo_user=None):
    # request = get_request()

    clusters = ClusterDefinitionsApi()
    clusters.api_client.host = settings.DIBBS['urls']['rm']
    # relay_swagger(clusters, request)
    _attach_auth_header(clusters, obo_user)

    return clusters.clusters_id_new_account_post(id)


def credentials_get(obo_user=None):
    # request = get_request()

    credentials = CredentialsApi()
    credentials.api_client.host = settings.DIBBS['urls']['rm']
    # relay_swagger(credentials, request)
    _attach_auth_header(credentials, obo_user)

    return credentials.credentials_get()


def operations_id_get(id, obo_user=None):
    # request = get_request()

    operations = OperationsApi()
    operations.api_client.host = settings.DIBBS['urls']['or']
    # relay_swagger(operations, request)
    _attach_auth_header(operations, obo_user)

    return operations.operations_id_get(id=id)


def operationversions_id_get(id, obo_user=None):
    # request = get_request()

    operation_versions = OperationVersionsApi()
    operation_versions.api_client.host = settings.DIBBS['urls']['or']
    # relay_swagger(operation_versions, request)
    _attach_auth_header(operation_versions, obo_user)

    return operation_versions.operationversions_id_get(id=id)
