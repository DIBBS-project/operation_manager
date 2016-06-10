from pdapp.permissions import IsOwnerOrReadOnly

# Create your views here.

from django.contrib.auth.models import User
from pdapp.models import Execution
from pdapp.serializers import ExecutionSerializer, UserSerializer
from rest_framework import viewsets, permissions, status

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


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
        serializer.save(author=self.request.user)

    # Override to set the user of the request using the credentials provided to perform the request.
    def create(self, request, *args, **kwargs):

        from prapp_client.apis import ProcessDefinitionsApi
        from process_record import set_variables, set_files, fileneames_dictionary, get_bash_script
        import json

        data2 = request.data
        data2[u'author'] = request.user.id
        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)

        # Check that the process definition exists
        process_id = data2[u'process_id']
        ret = ProcessDefinitionsApi().processdef_id_get(id=process_id)

        # Get all the required information
        record = json.loads(ret.adapters)
        parameters = json.loads(data2[u'parameters'])
        files = json.loads(data2[u'files'])
        fileneames = fileneames_dictionary(files)
        record = set_variables(record, parameters)
        record = set_files(record, fileneames)

        script = get_bash_script(record, ret.archive_url, files, fileneames)
        print (script)

        # Save in the database
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Call Mr Cluster

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
