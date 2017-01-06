# coding: utf-8
'''
Clients. They don't need any reconfiguring (apart from maybe the agent
clients?), so just one & done 'em.
'''

from common_dibbs.clients.ar_client.apis import ApplianceImplementationsApi
from common_dibbs.clients.or_client.apis import (OperationsApi,
                                                 OperationVersionsApi)
from common_dibbs.clients.rm_client.apis import (ClusterDefinitionsApi,
                                                 CredentialsApi,
                                                 HostDefinitionsApi)
from common_dibbs.clients.rm_client.rest import ApiException as RmApiException
from common_dibbs.misc import configure_basic_authentication

from settings import Settings


SETTINGS = Settings()

operations = OperationsApi()
operations.api_client.host = "%s" % (SETTINGS.operation_registry_url,)
configure_basic_authentication(operations, "admin", "pass")

operation_versions = OperationVersionsApi()
operation_versions.api_client.host = "%s" % (SETTINGS.operation_registry_url,)
configure_basic_authentication(operation_versions, "admin", "pass")

appliance_implementations = ApplianceImplementationsApi()
appliance_implementations.api_client.host = "%s" % (SETTINGS.appliance_registry_url,)
configure_basic_authentication(appliance_implementations, "admin", "pass")

credentials = CredentialsApi()
credentials.api_client.host = "%s" % (SETTINGS.resource_manager_url,)
configure_basic_authentication(credentials, "admin", "pass")

clusters = ClusterDefinitionsApi()
clusters.api_client.host = "%s" % (SETTINGS.resource_manager_url,)
configure_basic_authentication(clusters, "admin", "pass")
