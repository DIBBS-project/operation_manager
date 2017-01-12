# coding: utf-8
'''
Clients. They don't need any reconfiguring (apart from maybe the agent
clients?), so just one & done 'em.
'''
from __future__ import absolute_import, print_function

from django.conf import settings

from common_dibbs.clients.ar_client.apis import ApplianceImplementationsApi
from common_dibbs.clients.or_client.apis import (OperationsApi,
                                                 OperationVersionsApi)
from common_dibbs.clients.rm_client.apis import (ClusterDefinitionsApi,
                                                 CredentialsApi,
                                                 HostDefinitionsApi)
from common_dibbs.clients.rm_client.rest import ApiException as RmApiException
from common_dibbs.misc import configure_basic_authentication

operations = OperationsApi()
operations.api_client.host = settings.DIBBS['urls']['or']
configure_basic_authentication(operations, "admin", "pass")

operation_versions = OperationVersionsApi()
operation_versions.api_client.host = settings.DIBBS['urls']['or']
configure_basic_authentication(operation_versions, "admin", "pass")

appliance_implementations = ApplianceImplementationsApi()
appliance_implementations.api_client.host = settings.DIBBS['urls']['ar']
configure_basic_authentication(appliance_implementations, "admin", "pass")

credentials = CredentialsApi()
credentials.api_client.host = settings.DIBBS['urls']['rm']
configure_basic_authentication(credentials, "admin", "pass")

clusters = ClusterDefinitionsApi()
clusters.api_client.host = settings.DIBBS['urls']['rm']
configure_basic_authentication(clusters, "admin", "pass")
