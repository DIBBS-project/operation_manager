import requests, os
import json
import uuid
import logging
import os
import re
import time
import sys
import thread
import base64


def configure_basic_authentication(swagger_client, username, password):
    authentication_string = "%s:%s" % (username, password)
    base64_authentication_string = base64.b64encode(bytes(authentication_string))
    header_key = "Authorization"
    header_value = "Basic %s" % (base64_authentication_string, )
    swagger_client.api_client.default_headers[header_key] = header_value


def get_clusters(resource_provisioner_url):
    r = requests.get('%s/clusters/' % resource_provisioner_url, headers={})
    response = json.loads(r.content)
    return response


def deploy_cluster(execution, appliance, resource_provisioner_url):
    from rp_client.apis import ClusterDefinitionsApi

    execution.status = "DEPLOYING"
    execution.status_info = "Creating virtual cluster"
    execution.save()

    logging.info("creating the logical cluster")
    cluster_creation_data = {"user_id": "1",  # TODO: Remove (update the swagger client to >= 0.1.11 first)
                             "appliance": appliance,
                             "name": "MyHadoopCluster"}

    clusters_client = ClusterDefinitionsApi()
    clusters_client.api_client.host = "%s" % (resource_provisioner_url,)
    configure_basic_authentication(clusters_client, "admin", "pass")

    response = clusters_client.clusters_post(data=cluster_creation_data)
    cluster_id = response.id

    # Add a master node to the cluster
    execution.status_info = "Adding master node"
    execution.save()

    logging.info("adding a new node (master) to the cluster %s" % (cluster_id,))
    node_addition_data = {"cluster_id": cluster_id}
    r = requests.post('%s/hosts/' % resource_provisioner_url,
                      data=json.dumps(node_addition_data))

    nb_nodes = 2
    for i in range(1, nb_nodes):
        logging.info("adding a new node (slave %s/%s) to the cluster %s" % (i, nb_nodes-1, cluster_id))
        # Add a slave node to the cluster
        execution.status_info = "Adding slave node (%s/%s)" % (i, nb_nodes-1)
        execution.save()

        logging.info("adding a new node (slave) to the cluster %s" % (cluster_id,))
        r = requests.post('%s/hosts/' % resource_provisioner_url,
                          data=json.dumps(node_addition_data))

    execution.status = "DEPLOYED"
    execution.status_info = ""
    execution.save()

    # Get the cluster description
    logging.info("get a description of the cluster %s" % cluster_id)
    description = ClusterDefinitionsApi().clusters_id_get(id=cluster_id)

    logging.info("description will be returned %s" % description)
    return description


# def run_process(cluster, script, callback_url, execution):
#
#     execution.status = "PREPARING"
#     execution.status_info = ""
#     execution.save()
#
#     request_uuid = str(uuid.uuid4())
#
#     user = "user"
#     password = "password"
#
#     logging.info("launching script (request_uuid=%s)" % (request_uuid,))
#
#     execution.status_info = "Generating temporary folder"
#     execution.save()
#
#     def create_file(path, fdata):
#         # Delete file if it already exists
#         if os.path.exists(path):
#             os.remove(path)
#         englobing_folder = "/".join(path.split("/")[:-1])
#         if not os.path.exists(englobing_folder):
#             os.makedirs(englobing_folder)
#         # Write data in a new file
#         with open(path, "w+") as f:
#             f.write(fdata)
#         return True
#
#     execution.status_info = "Generating script.sh"
#     execution.save()
#
#     script_path = "tmp/%s/script_%s.sh" % (user, request_uuid)
#
#     create_file(script_path, script)
#     logging.info("generated script in %s" % script_path)
#
#     REMOTE_HADOOP_WEBSERVICE_HOST="http://%s:8000" % (cluster.master_node_ip,)
#
#     execution.status_info = "Creating user"
#     execution.save()
#
#     logging.info("ensuring that the user %s exists" % (user,))
#     data = {
#         "username": user,
#         "password": password
#     }
#     r = requests.post('%s/register_new_user/' % (REMOTE_HADOOP_WEBSERVICE_HOST,), data=data)
#     response = json.loads(r.content)
#
#     headers = {
#         "username": user,
#         "password": password
#     }
#
#     logging.info("generating a new token for %s" % (user,))
#     r = requests.get('%s/generate_new_token/' % (REMOTE_HADOOP_WEBSERVICE_HOST,), headers=headers)
#     response = json.loads(r.content)
#     token = response["token"]
#
#     logging.info("TOKEN: %s" % (token,))
#
#     headers = {
#         "token": token
#     }
#
#     execution.status_info = "Cleaning/uploading files"
#     execution.save()
#
#     # Clean output file in FS folder to prevent interference between tests
#     logging.info("cleaning the existing script.sh file (if it exists)")
#     requests.get('%s/fs/rm/script.sh/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
#     # curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/rm/test.sh/
#
#     # Clean output file in FS folder to prevent interference between tests
#     logging.info("cleaning the existing output.txt file (if it exists)")
#     requests.get('%s/fs/rm/output.txt/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
#     # curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/rm/output.txt/
#
#     # Upload local files to the application
#     logging.info("uploading a new version of script.sh")
#     files = {
#         "data": open(script_path, 'rb')
#     }
#     r = requests.post('%s/fs/upload/script.sh/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers, files=files)
#     # curl --header "token: $TOKEN" -i -X POST -F 'data=@test.sh' $REMOTE_HADOOP_WEBSERVICE_HOST/fs/upload/test.sh/
#     print (r)
#
#     execution.status = "RUNNING"
#     execution.status_info = "Executing the job"
#     execution.save()
#
#     # Run "test.sh" with bash
#     logging.info("running script.sh")
#     r = requests.get('%s/fs/run/script.sh/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
#     # curl --header "token: $TOKEN" -i -X GET  $REMOTE_HADOOP_WEBSERVICE_HOST/fs/run/test.sh/
#     print (r)
#
#     # Download the "output.txt" file
#     execution.status = "COLLECTING"
#     execution.status_info = "Getting output file"
#     execution.save()
#
#     logging.info("downloading the output")
#     r = requests.get('%s/fs/download/output.txt/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
#     # curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/download/out.txt/
#     print (r)
#
#     # Sending the result to the callback url
#     if callback_url:
#         logging.info("calling the callback (%s)" % callback_url)
#         execution.status_info = "Sending output to %s" % (callback_url)
#         execution.save()
#
#         r = requests.post(callback_url, data=r.content)
#         print (r)
#
#     execution.output_location = '%s/fs/download/output.txt/?token=%s' % (REMOTE_HADOOP_WEBSERVICE_HOST, token)
#     execution.status = "FINISHED"
#     execution.status_info = ""
#     execution.save()
#
#     return True


def create_temporary_user(cluster, execution, resource_provisioner_url):

    from rp_client.apis import ClusterDefinitionsApi, CredentialsApi

    cluster_id = cluster.id if not isinstance(cluster, dict) else cluster["id"]

    execution.status = "PREPARING"
    execution.status_info = ""
    execution.save()

    logging.info("creating a temporary user on cluster %s" % (cluster,))

    execution.status_info = "Creating a temporary user on cluster %s" % (cluster,)
    execution.save()

    clusters_client = ClusterDefinitionsApi()
    clusters_client.api_client.host = "%s" % (resource_provisioner_url,)
    configure_basic_authentication(clusters_client, "admin", "pass")

    result = clusters_client.clusters_id_new_account_post(cluster_id)

    execution.status_info = "Temporary user created"
    execution.save()

    return result


def run_process_new(cluster, script, callback_url, execution, credentials):

    from pma_client.apis import OpsApi, UsersApi
    from pma_client.api_client import ApiClient
    from pma_client.configure import configure_auth_basic

    master_node_ip = cluster.master_node_ip if not isinstance(cluster, dict) else cluster["master_node_ip"]

    execution.status = "PREPARING"
    execution.status_info = ""
    execution.save()

    request_uuid = str(uuid.uuid4())

    logging.info("launching script (request_uuid=%s)" % (request_uuid,))

    execution.status_info = "Generating temporary folder"
    execution.save()

    def create_file(path, fdata):
        # Delete file if it already exists
        if os.path.exists(path):
            os.remove(path)
        englobing_folder = "/".join(path.split("/")[:-1])
        if not os.path.exists(englobing_folder):
            os.makedirs(englobing_folder)
        # Write data in a new file
        with open(path, "w+") as f:
            f.write(fdata)
        return True

    execution.status_info = "Generating script.sh"
    execution.save()

    ops_client = OpsApi()
    ops_client.api_client.host = "http://%s:8011" % (master_node_ip,)

    username = credentials.username if not isinstance(credentials, dict) else credentials["username"]
    password = credentials.password if not isinstance(credentials, dict) else credentials["password"]

    configure_basic_authentication(ops_client, username, password)

    ops_data = {
        "script": script,
        "callback_url": callback_url
    }

    logging.info("creation the operation %s" % (ops_data,))
    execution.status_info = "Creating the Operation"
    execution.save()

    result = ops_client.ops_post(data=ops_data)

    if not hasattr(result, "id"):
        msg = "Could not create operation (%s) on the master node (%s)" % (ops_data, master_node_ip)
        logging.error("%s, aborting..." % (msg, master_node_ip))
        execution.status = "ERROR"
        execution.status_info = "%s" % (msg, )
        execution.save()
        raise Exception(msg)

    operation = result

    logging.info("running the operation %s" % (ops_data,))
    execution.status = "RUNNING"
    execution.status_info = "Executing the operation (%s on %s)" % (operation.id, master_node_ip)
    execution.save()

    ops_client.ops_id_run_op_post(operation.id)

    # # Run "test.sh" with bash
    # logging.info("running script.sh")
    # r = requests.get('%s/fs/run/script.sh/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
    # # curl --header "token: $TOKEN" -i -X GET  $REMOTE_HADOOP_WEBSERVICE_HOST/fs/run/test.sh/
    # print (r)

    # Download the "output.txt" file
    execution.status = "COLLECTING"
    execution.status_info = "Getting output file"
    execution.save()

    # logging.info("downloading the output")
    # r = requests.get('%s/fs/download/output.txt/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
    # # curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/download/out.txt/
    # print (r)
    #
    # # Sending the result to the callback url
    # if callback_url:
    #     logging.info("calling the callback (%s)" % callback_url)
    #     execution.status_info = "Sending output to %s" % (callback_url)
    #     execution.save()
    #
    #     r = requests.post(callback_url, data=r.content)
    #     print (r)

    # execution.output_location = '%s/fs/download/output.txt/?token=%s' % (REMOTE_HADOOP_WEBSERVICE_HOST, token)
    execution.status = "FINISHED"
    execution.status_info = ""
    execution.save()

    return True
