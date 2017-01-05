from django.contrib.auth.models import User
from omapp.models import Execution, Instance
from omapp.serializers import ExecutionSerializer, InstanceSerializer, UserSerializer
from rest_framework import viewsets, permissions, status
from django.views.decorators.csrf import csrf_exempt

from common_dibbs.clients.or_client.apis import OperationsApi, OperationVersionsApi
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


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
    return Response({"status": "success"}, status=status.HTTP_202_ACCEPTED)
