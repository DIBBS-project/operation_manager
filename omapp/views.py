from django.contrib.auth.models import User
from omapp.models import Execution, Instance
from omapp.serializers import ExecutionSerializer, InstanceSerializer, UserSerializer
from rest_framework import viewsets, permissions, status
from django.views.decorators.csrf import csrf_exempt

from common_dibbs.clients.or_client.apis import OperationsApi, OperationVersionsApi
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from sched.scheduling_policies import DummySchedulingPolicy as SchedulingPolicy
from requests.exceptions import ConnectionError

from settings import Settings
import base64
import logging
import traceback
import time
from common_dibbs.misc import configure_basic_authentication
from common_dibbs.clients.or_client.apis import OperationsApi
from common_dibbs.clients.ar_client.apis import ApplianceImplementationsApi
from common_dibbs.clients.rm_client.apis import CredentialsApi
import json

logging.basicConfig(level=logging.INFO)


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'executions': reverse('execution-list', request=request, format=format)
    })


def filter_clusters_in_site(clusters, hints):
    # Create a client for ApplianceImplementations
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
    configure_basic_authentication(appliance_implementations_client, "admin", "pass")

    # Create a client for Credentials
    credentials_client = CredentialsApi()
    credentials_client.api_client.host = "%s" % (Settings().resource_manager_url,)
    configure_basic_authentication(appliance_implementations_client, "admin", "pass")

    all_credentials = credentials_client.credentials_get()

    sites = []
    credentials = hints["credentials"]
    for credential in credentials:
        matching_credentials = filter(lambda cred: cred.name == credential, all_credentials)
        if len(matching_credentials) == 0:
            continue
        matching_credential = matching_credentials[0]
        if matching_credential.site_name not in sites:
            sites += [matching_credential.site_name]

    results = []
    for cluster in clusters:
        if cluster.appliance_impl == "":
            continue
        appliance_impl = appliance_implementations_client.appliances_impl_name_get(cluster.appliance_impl)
        if appliance_impl.site in sites or "*" in credentials:
            results += [cluster]
    return results


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class InstanceViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Instance.objects.all()
    serializer_class = InstanceSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    # Override to set the user of the request using the credentials provided to perform the request.
    def create(self, request, *args, **kwargs):

        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'author'] = request.user.id
        data2[u'executions'] = {}
        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)

        # Create a client for Operations
        operations_client = OperationsApi()
        operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
        configure_basic_authentication(operations_client, "admin", "pass")

        # Check that the process definition exists
        process_definition_id = data2[u'process_definition_id']

        operations_client.operations_id_get(id=process_definition_id)

        # Check that the parameters are valid JSON
        if data2[u'parameters']:
            try:
                json.loads(data2[u'parameters'])
            except:
                return Response({"error": "Invalid format for parameters"}, status=status.HTTP_400_BAD_REQUEST)

        if data2[u'files']:
            try:
                json.loads(data2[u'files'])
            except:
                return Response({"error": "Invalid format for files"}, status=status.HTTP_400_BAD_REQUEST)

        # Save in the database
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ExecutionViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Execution.objects.all()
    serializer_class = ExecutionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    # Override to set the user of the request using the credentials provided to perform the request.
    def create(self, request, *args, **kwargs):
        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'status'] = "PENDING"
        data2[u'status_info'] = ""
        data2[u'author'] = request.user.id
        data2[u'output_location'] = ""
        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)

        # Save in the database
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@api_view(['GET'])
@csrf_exempt
def run_execution(request, pk):
    from process_record import set_variables, set_files, fileneames_dictionary, get_bash_script
    from omapp.core import get_clusters, deploy_cluster
    # from omapp.core import run_process
    from omapp.core import run_process_new as run_process
    from omapp.core import create_temporary_user as create_temporary_user
    import json

    try:
        execution = Execution.objects.get(pk=pk)
    except:
        traceback.print_exc()
        return Response({"status": "failed"}, status=status.HTTP_404_NOT_FOUND)

    try:
        execution.status = "INIT"
        execution.status_info = "Checking parameters"
        execution.save()

        # Create a client for Operations
        operations_client = OperationsApi()
        operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
        configure_basic_authentication(operations_client, "admin", "pass")

        # Create a client for OperationVersions
        operation_versions_client = OperationVersionsApi()
        operation_versions_client.api_client.host = "%s" % (Settings().operation_registry_url,)
        configure_basic_authentication(operation_versions_client, "admin", "pass")

        # Check that the process definition exists
        operation_instance = execution.operation_instance
        operation = operations_client.operations_id_get(id=operation_instance.process_definition_id)

        # FIXME: the chosen process implementation is always the first one
        # UPDATE: New architecture: No process implementation but process version, it will be fixed when changing this
        operation_version_id = operation.implementations[0]
        operation_version = operation_versions_client.operationversions_id_get(id=operation_version_id)

        if operation_version.output_parameters == "":
            operation_version.output_parameters = {}
        else:
            operation_version.output_parameters = json.loads(operation_version.output_parameters)

        # Get all the required information
        appliance = operation_version.appliance
        parameters = json.loads(execution.operation_instance.parameters)
        files = json.loads(execution.operation_instance.files)

        filenames = fileneames_dictionary(files)
        set_variables(operation_version, parameters)
        set_files(operation_version, filenames)

        script = get_bash_script(operation_version, files, filenames)
        print (script)

        callback_url = execution.callback_url

    except:
        traceback.print_exc()
        execution.status = "FAILED"
        execution.status_info = "Incorrect process definition or parameters"
        execution.save()
        return Response({"status": "failed"}, status=status.HTTP_412_PRECONDITION_FAILED)

    try:
        # Call Mr Cluster
        clusters = get_clusters(Settings().resource_manager_url)
        hints = None
        if execution.hints != "{}":
            hints = eval(execution.hints)
            clusters = filter_clusters_in_site(clusters, hints)
        # HINT INSERTION: Here we could use hints to select the right cluster
        cluster_to_use = SchedulingPolicy().decide_cluster_deployment(appliance, clusters, force_new=execution.force_spawn_cluster!='', hints=hints)
        if cluster_to_use is None:
            logging.info("Creating a virtual cluster")
            cluster_to_use = deploy_cluster(execution, appliance, Settings().resource_manager_url, hints=hints)

    except:
        traceback.print_exc()
        execution.status = "FAILED"
        execution.status_info = "Error while deploying the cluster"
        execution.save()
        return Response({"status": "failed"}, status=status.HTTP_412_PRECONDITION_FAILED)

    retry_count = 0
    credentials = None
    while not credentials and retry_count < 10:
        try:
            logging.info("Creating a temporary a process on the cluster %s" % cluster_to_use)
            credentials = create_temporary_user(cluster_to_use, execution, Settings().resource_manager_url)
        except ConnectionError as e:
            logging.info("The deployed ressources seems to not be ready yet, I'm giving more time (5 seconds) to start!")
            retry_count += 1
            time.sleep(5)
        except:
            traceback.print_exc()
            execution.status = "FAILED"
            execution.status_info = "Error while creating the temporary user"
            execution.save()
            return Response({"status": "failed"}, status=status.HTTP_412_PRECONDITION_FAILED)

    if not credentials:
        return Response({"status": "failed"}, status=status.HTTP_412_PRECONDITION_FAILED)

    retry_count = 0
    while retry_count < 10:
        try:
            logging.info("Running a process on the cluster %s" % cluster_to_use)
            run_process(cluster_to_use, script, callback_url, execution, credentials)

            return Response({"status": "success"}, status=status.HTTP_202_ACCEPTED)
        except ConnectionError as e:
            logging.info("The deployed ressources seems to not be ready yet, I'm giving more time (5 seconds) to start!")
            retry_count += 1
            time.sleep(5)
        except:
            traceback.print_exc()
            execution.status = "FAILED"
            execution.status_info = "Error while running the process"
            execution.save()
            return Response({"status": "failed"}, status=status.HTTP_412_PRECONDITION_FAILED)
