from pdapp.permissions import IsOwnerOrReadOnly

# Create your views here.

from django.contrib.auth.models import User
from pdapp.models import Execution
from pdapp.serializers import ExecutionSerializer, UserSerializer
from rest_framework import viewsets, permissions, status
from django.views.decorators.csrf import csrf_exempt

from pdapp.pr_client.apis import ProcessDefinitionsApi, ProcessImplementationApi
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from settings import Settings

import logging

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


class ExecutionViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Execution.objects.all()
    serializer_class = ExecutionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    # Override to set the user of the request using the credentials provided to perform the request.
    def create(self, request, *args, **kwargs):

        from pr_client.apis import ProcessDefinitionsApi

        # data2 = request.data
        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'status'] = "PENDING"
        data2[u'status_info'] = ""
        data2[u'author'] = request.user.id
        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)

        # Check that the process definition exists
        process_id = data2[u'process_id']
        ProcessDefinitionsApi().processdefs_id_get(id=process_id)

        # Save in the database
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@api_view(['GET'])
@csrf_exempt
def run_execution(request, pk):
    from pr_client.apis import ProcessDefinitionsApi
    from process_record import set_variables, set_files, fileneames_dictionary, get_bash_script
    from pdapp.core import deploy_cluster, run_process
    import json

    try:
        execution = Execution.objects.get(pk=pk)
    except:
        return Response({"status": "failed"}, status=status.HTTP_404_NOT_FOUND)

    try:
        execution.status = "INIT"
        execution.status_info = "Checking parameters"
        execution.save()

        # Check that the process definition exists
        process_id = execution.process_id
        process_impl = ProcessImplementationApi().processimpls_id_get(id=execution.process_id)
        process_def = ProcessDefinitionsApi().processdefs_id_get(id=process_impl.process_definition)
        # ret = ProcessDefinitionsApi().processdefs_id_get(id=process_id)

        if process_def.argv == "":
            process_def.argv = []
        else:
            process_def.argv = json.loads(process_def.argv)
        if process_impl.environment == "":
            process_impl.environment = {}
        else:
            process_impl.environment = json.loads(process_impl.environment)
        if process_def.output_parameters == "":
            process_def.output_parameters = {}
        else:
            process_def.output_parameters = json.loads(process_def.output_parameters)

        # Get all the required information
        appliance = process_impl.appliance
        parameters = json.loads(execution.parameters)
        files = json.loads(execution.files)
        filenames = fileneames_dictionary(files)
        (process_def, process_impl) = set_variables(process_def, process_impl, parameters)
        (process_def, process_impl) = set_files(process_def, process_impl, filenames)

        script = get_bash_script(process_def, process_impl, files, filenames)
        print (script)

        callback_url = execution.callback_url

        # Call Mr Cluster

        logging.info("Creating a virtual cluster")
        cluster = deploy_cluster(execution, appliance, Settings().resource_provisioner_url)

        logging.info("Running a process on the cluster %s" % (cluster))
        run_process(cluster, script, callback_url, execution)

        return Response({"status": "success"}, status=status.HTTP_202_ACCEPTED)

    except:
        execution.status = "FAILED"
        execution.status_info = "Incorrect process definition or parameters"
        execution.save()
        return Response({"status": "failed"}, status=status.HTTP_412_PRECONDITION_FAILED)
