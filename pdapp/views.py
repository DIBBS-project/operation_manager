from django.contrib.auth.models import User
from pdapp.models import Execution, ProcessInstance
from pdapp.serializers import ExecutionSerializer, ProcessInstanceSerializer, UserSerializer
from rest_framework import viewsets, permissions, status
from django.views.decorators.csrf import csrf_exempt

from pdapp.pr_client.apis import ProcessImplementationsApi, ProcessDefinitionsApi
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from sched.scheduling_policies import DummySchedulingPolicy as SchedulingPolicy
from requests.exceptions import ConnectionError

from settings import Settings

import logging
import traceback
import time
logging.basicConfig(level=logging.INFO)


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'executions': reverse('execution-list', request=request, format=format)
    })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ProcessInstanceViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = ProcessInstance.objects.all()
    serializer_class = ProcessInstanceSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    # Override to set the user of the request using the credentials provided to perform the request.
    def create(self, request, *args, **kwargs):
        from pr_client.apis import ProcessDefinitionsApi
        import json

        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'author'] = request.user.id
        data2[u'executions'] = {}
        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)

        # Check that the process definition exists
        process_definition_id = data2[u'process_definition_id']
        ProcessDefinitionsApi().processdefs_id_get(id=process_definition_id)

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
    from pdapp.core import get_clusters, deploy_cluster, run_process
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

        # Check that the process definition exists
        process_instance = execution.process_instance
        process_definition = ProcessDefinitionsApi().processdefs_id_get(id=process_instance.process_definition_id)

        # FIXME: the chosen process implementation is always the first one
        # UPDATE: New architecture: No process implementation but process version, it will be fixed when changing this
        process_impl_id = process_definition.implementations[0]
        process_impl = ProcessImplementationsApi().processimpls_id_get(id=process_impl_id)

        if process_impl.output_parameters == "":
            process_impl.output_parameters = {}
        else:
            process_impl.output_parameters = json.loads(process_impl.output_parameters)

        # Get all the required information
        appliance = process_impl.appliance
        parameters = json.loads(execution.process_instance.parameters)
        files = json.loads(execution.process_instance.files)

        filenames = fileneames_dictionary(files)
        set_variables(process_impl, parameters)
        set_files(process_impl, filenames)

        script = get_bash_script(process_impl, files, filenames)
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
        clusters = get_clusters(Settings().resource_provisioner_url)
        cluster_to_use = SchedulingPolicy().decide_cluster_deployment(appliance, clusters, force_new=execution.force_spawn_cluster!='')
        if cluster_to_use is None:
            logging.info("Creating a virtual cluster")
            cluster_to_use = deploy_cluster(execution, appliance, Settings().resource_provisioner_url)

    except:
        traceback.print_exc()
        execution.status = "FAILED"
        execution.status_info = "Error while deploying the cluster"
        execution.save()
        return Response({"status": "failed"}, status=status.HTTP_412_PRECONDITION_FAILED)

    retry_count = 0
    while retry_count < 10:
        try:
            logging.info("Running a process on the cluster %s" % cluster_to_use)
            run_process(cluster_to_use, script, callback_url, execution)

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
