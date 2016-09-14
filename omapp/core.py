import requests, os
import json
import uuid
import logging
import os
import re
import time
import sys
import thread
from common_dibbs.misc import configure_basic_authentication

from common_dibbs.clients.oma_client.apis import OpsApi, UsersApi
from common_dibbs.clients.oma_client.api_client import ApiClient
from common_dibbs.clients.rm_client.apis import ClusterDefinitionsApi, HostDefinitionsApi
from common_dibbs.clients.rm_client.apis import ClusterDefinitionsApi, CredentialsApi
from common_dibbs.clients.rm_client.apis import ClusterDefinitionsApi, HostDefinitionsApi


def get_clusters(resource_manager_url):
    # Create a client for Clusters
    clusters_client = ClusterDefinitionsApi()
    clusters_client.api_client.host = "%s" % (resource_manager_url,)
    configure_basic_authentication(clusters_client, "admin", "pass")

    response = clusters_client.clusters_get()
    return response


def deploy_cluster(execution, appliance, resource_manager_url, hints=None):

    execution.status = "DEPLOYING"
    execution.status_info = "Creating virtual cluster"
    execution.save()

    logging.info("creating the logical cluster")
    cluster_creation_data = {"user_id": "1",  # TODO: Remove (update the swagger client to >= 0.1.11 first)
                             "appliance": appliance,
                             "name": "MyHadoopCluster"}

    if hints is not None:
        cluster_creation_data["hints"] = json.dumps(hints)

    # Create a client for ClusterDefinitions
    clusters_client = ClusterDefinitionsApi()
    clusters_client.api_client.host = "%s" % (resource_manager_url,)
    configure_basic_authentication(clusters_client, "admin", "pass")

    # HINT INSERTION: Add a hint to this function to help to chose the right site
    response = clusters_client.clusters_post(data=cluster_creation_data)
    cluster_id = response.id

    # Add a master node to the cluster
    execution.status_info = "Adding master node"
    execution.save()

    logging.info("adding a new node (master) to the cluster %s" % (cluster_id,))
    hosts_client = HostDefinitionsApi()
    hosts_client.api_client.host = "%s" % (resource_manager_url,)
    configure_basic_authentication(hosts_client, "admin", "pass")

    node_addition_data = {"cluster_id": cluster_id}
    hosts_client.hosts_post(data=node_addition_data)

    nb_nodes = 2
    for i in range(1, nb_nodes):
        logging.info("adding a new node (slave %s/%s) to the cluster %s" % (i, nb_nodes-1, cluster_id))
        # Add a slave node to the cluster
        execution.status_info = "Adding slave node (%s/%s)" % (i, nb_nodes-1)
        execution.save()

        logging.info("adding a new node (slave) to the cluster %s" % (cluster_id,))
        hosts_client.hosts_post(data=node_addition_data)

    execution.status = "DEPLOYED"
    execution.status_info = ""
    execution.save()

    # Get the cluster description
    logging.info("get a description of the cluster %s" % cluster_id)
    description = clusters_client.clusters_id_get(id=cluster_id)

    logging.info("description will be returned %s" % description)
    return description


def create_temporary_user(cluster, execution, resource_manager_url):
    cluster_id = cluster.id if not isinstance(cluster, dict) else cluster["id"]

    execution.status = "PREPARING"
    execution.status_info = ""
    execution.save()

    logging.info("creating a temporary user on cluster %s" % (cluster,))

    execution.status_info = "Creating a temporary user on cluster %s" % (cluster,)
    execution.save()

    # Create a client for ClusterDefinitions
    clusters_client = ClusterDefinitionsApi()
    clusters_client.api_client.host = "%s" % (resource_manager_url,)
    configure_basic_authentication(clusters_client, "admin", "pass")

    result = clusters_client.clusters_id_new_account_post(cluster_id)

    execution.status_info = "Temporary user created"
    execution.save()

    return result


def run_process_new(cluster, script, callback_url, execution, credentials):
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

    # Create a client for Operations
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
