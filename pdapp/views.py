from pdapp.permissions import IsOwnerOrReadOnly

# Create your views here.

from django.contrib.auth.models import User
from pdapp.models import Execution
from pdapp.serializers import ExecutionSerializer, UserSerializer
from rest_framework import viewsets, permissions, status

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

import requests, time
import json
import uuid
import logging
import os

MISTER_CLUSTER_URL = "http://127.0.0.1:8002"
MISTER_CLUSTER_TOKEN = "849fcb45-f666-4642-8c8b-f16973fb29fa"

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

        from prapp_client.apis import ProcessDefinitionsApi
        from process_record import set_variables, set_files, fileneames_dictionary, get_bash_script
        import json

        # data2 = request.data
        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'author'] = request.user.id
        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)

        # Check that the process definition exists
        process_id = data2[u'process_id']
        ret = ProcessDefinitionsApi().processdef_id_get(id=process_id)

        # Get all the required information
        appliance_id = ret.appliance_id
        record = json.loads(ret.adapters)
        parameters = json.loads(data2[u'parameters'])
        files = json.loads(data2[u'files'])
        filenames = fileneames_dictionary(files)
        record = set_variables(record, parameters)
        record = set_files(record, filenames)

        script = get_bash_script(record, ret.archive_url, files, filenames)
        print (script)

        # Save in the database
        execution = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        callback_url = data2["callback_url"]

        # Call Mr Cluster
        def deploy_cluster(execution, cluster_id=None):

            headers = {
                "TOKEN": execution.mrcluster_token
            }

            if cluster_id is None:

                execution.status = "DEPLOYING"
                execution.save()

                execution.status_info = "Creating virtual cluster"
                execution.save()

                logging.info("creating the logical cluster")
                cluster_creation_data = {"user_id": "1","site_id": "1", "software_id": appliance_id, "name": "MyHadoopCluster"}
                r = requests.post('%s/clusters/' % (MISTER_CLUSTER_URL), data=json.dumps(cluster_creation_data), headers=headers)

                response = json.loads(r.content)
                cluster_id = response["cluster_id"]

                # Add a master node to the cluster
                execution.status_info = "Adding master node"
                execution.save()

                logging.info("adding a new node (master) to the cluster %s" % (cluster_id))
                node_addition_data = {"cluster_id": cluster_id}
                r = requests.post('%s/hosts/' % (MISTER_CLUSTER_URL), data=json.dumps(node_addition_data), headers=headers)

                # Add a slave node to the cluster
                execution.status_info = "Adding slave node"
                execution.save()

                logging.info("adding a new node (slave) to the cluster %s" % (cluster_id))
                r = requests.post('%s/hosts/' % (MISTER_CLUSTER_URL), data=json.dumps(node_addition_data), headers=headers)

            execution.status = "DEPLOYED"
            execution.status_info = ""
            execution.save()

            # Get the cluster description
            logging.info("get a description of the cluster %s" % (cluster_id))
            r = requests.get('%s/clusters/%s/' % (MISTER_CLUSTER_URL, cluster_id), headers=headers)
            description = json.loads(r.content)

            logging.info("description will be returned %s" % (description))
            return description

        logging.info("Creating a virtual cluster")
        cluster = deploy_cluster(execution)

        def run_process(cluster, script, callback_url, execution):

            execution.status = "PREPARING"
            execution.status_info = ""
            execution.save()

            request_uuid = str(uuid.uuid4())

            user = "user"
            password = "password"

            logging.info("launching script (request_uuid=%s)" % (request_uuid))

            execution.status_info = "Generating temporary folder"
            execution.save()

            def create_file(path, data):
                # Delete file if it already exists
                if os.path.exists(path):
                    os.remove(path)
                englobing_folder = "/".join(path.split("/")[:-1])
                if not os.path.exists(englobing_folder):
                    os.makedirs(englobing_folder)
                # Write data in a new file
                with open(path, "w+") as f:
                    f.write(data)
                return True

            execution.status_info = "Generating script.sh"
            execution.save()

            script_path = "tmp/%s/script_%s.sh" % (user, request_uuid)

            create_file(script_path, script)
            logging.info("generated script in %s" % (script_path))

            REMOTE_HADOOP_WEBSERVICE_HOST="http://%s:8000" % (cluster["master_node_ip"])

            execution.status_info = "Creating user"
            execution.save()

            logging.info("ensuring that the user %s exists" % (user))
            data = {
                "username": user,
                "password": password
            }
            r = requests.post('%s/register_new_user/' % (REMOTE_HADOOP_WEBSERVICE_HOST), data=data)
            response = json.loads(r.content)

            headers = {
                "username": user,
                "password": password
            }

            logging.info("generating a new token for %s" % (user))
            r = requests.get('%s/generate_new_token/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
            response = json.loads(r.content)
            token = response["token"]

            headers = {
                "token": token
            }

            execution.status_info = "Cleaning/uploading files"
            execution.save()

            # Clean output file in FS folder to prevent interference between tests
            logging.info("cleaning the existing script.sh file (if it exists)")
            requests.get('%s/fs/rm/script.sh/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
            # curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/rm/test.sh/

            # Clean output file in FS folder to prevent interference between tests
            logging.info("cleaning the existing output.txt file (if it exists)")
            requests.get('%s/fs/rm/output.txt/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
            # curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/rm/output.txt/

            # Upload local files to the application
            logging.info("uploading a new version of script.sh")
            files = {
                "data": open(script_path, 'rb')
            }
            r = requests.post('%s/fs/upload/script.sh/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers, files=files)
            # curl --header "token: $TOKEN" -i -X POST -F 'data=@test.sh' $REMOTE_HADOOP_WEBSERVICE_HOST/fs/upload/test.sh/
            print r

            execution.status = "RUNNING"
            execution.status_info = "Executing the job"
            execution.save()

            # Run "test.sh" with bash
            logging.info("running script.sh")
            r = requests.get('%s/fs/run/script.sh/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
            # curl --header "token: $TOKEN" -i -X GET  $REMOTE_HADOOP_WEBSERVICE_HOST/fs/run/test.sh/
            print r

            execution.status = "COLLECTING"
            execution.save()

            # Download the "output.txt" file
            execution.status_info = "Getting output file"
            execution.save()

            logging.info("downloading the output")
            r = requests.get('%s/fs/download/output.txt/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
            # curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/download/out.txt/
            print r

            # Sending the result to the callback url
            logging.info("calling the callback (%s)" % (callback_url))
            execution.status_info = "Sending output to %s" % (callback_url)
            execution.save()

            r = requests.post(callback_url, data=r.content)
            print r

            execution.output_location = '%s/fs/download/output.txt/?token=%s' % (REMOTE_HADOOP_WEBSERVICE_HOST, token)
            execution.status = "FINISHED"
            execution.status_info = ""
            execution.save()

            return True


        logging.info("Running a process on the cluster %s" % (cluster))
        run_process(cluster, script, callback_url, execution)


        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
