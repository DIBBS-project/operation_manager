import requests, os
import json
import uuid
import logging
import os
import re
import time
import sys
import thread
import traceback
from common_dibbs.misc import configure_basic_authentication
from requests.exceptions import ConnectionError
from rest_framework.response import Response
from rest_framework import status

from common_dibbs.clients.oma_client.apis import OpsApi, UsersApi
from common_dibbs.clients.oma_client.api_client import ApiClient
from common_dibbs.clients.rm_client.apis import ClusterDefinitionsApi, HostDefinitionsApi
from common_dibbs.clients.rm_client.apis import ClusterDefinitionsApi, CredentialsApi
from common_dibbs.clients.rm_client.apis import ClusterDefinitionsApi, HostDefinitionsApi

from settings import Settings
from common_dibbs.misc import configure_basic_authentication
from common_dibbs.clients.or_client.apis import OperationsApi
from common_dibbs.clients.or_client.apis import OperationsApi, OperationVersionsApi
from common_dibbs.clients.ar_client.apis import ApplianceImplementationsApi
from common_dibbs.clients.rm_client.apis import CredentialsApi
from sched.scheduling_policies import DummySchedulingPolicy as SchedulingPolicy


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


def get_clusters(resource_manager_url):
    # Create a client for Clusters
    clusters_client = ClusterDefinitionsApi()
    clusters_client.api_client.host = "%s" % (resource_manager_url,)
    configure_basic_authentication(clusters_client, "admin", "pass")

    response = clusters_client.clusters_get()
    return response


def deploy_cluster(execution, appliance, resource_manager_url, hints=None):

    from periodictasks import create_periodic_check_thread
    create_periodic_check_thread()

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


def run_process(cluster, script, callback_url, execution, credentials):
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


def mark_deploying_handler(transition, execution, user):
    from process_record import set_variables, set_files, fileneames_dictionary, get_bash_script
    from omapp.core import get_clusters, deploy_cluster
    # from omapp.core import run_process
    from omapp.core import run_process as run_process
    from omapp.core import create_temporary_user as create_temporary_user
    import json

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
            print("cluster_to_user: %s" % (cluster_to_use))
            execution.cluster_id = cluster_to_use.id
            execution.save()
        execution.cluster_id = cluster_to_use.id
        execution.save()
    except:
        traceback.print_exc()
        execution.status = "FAILED"
        execution.status_info = "Error while deploying the cluster"
        execution.save()
        return Response({"status": "failed"}, status=status.HTTP_412_PRECONDITION_FAILED)
    pass


def mark_ready_to_run_handler(transition, execution, user):
    pass


def mark_running_handler(transition, execution, user):
    from process_record import set_variables, set_files, fileneames_dictionary, get_bash_script
    from omapp.core import get_clusters, deploy_cluster
    # from omapp.core import run_process
    from omapp.core import run_process as run_process
    from omapp.core import create_temporary_user as create_temporary_user
    import json

    try:
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
        parameters = json.loads(execution.operation_instance.parameters)
        files = json.loads(execution.operation_instance.files)

        filenames = fileneames_dictionary(files)
        set_variables(operation_version, parameters)
        set_files(operation_version, filenames)

        script = get_bash_script(operation_version, files, filenames)
        # print (script)

        callback_url = execution.callback_url

        clusters = get_clusters(Settings().resource_manager_url)
        cluster_ids = map(lambda x: x.id, clusters)
        cluster_to_use = filter(lambda c: c.id == execution.cluster_id, clusters)[0]

        retry_count = 0
        credentials = None
        while not credentials and retry_count < 10:
            try:
                logging.info("Creating a temporary user on the cluster %s" % cluster_to_use)
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

        # print(execution)
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
    except:
        traceback.print_exc()
        logging.error("Could not launch the execution")
        pass
    pass


def mark_executed_handler(transition, execution, user):
    pass


def mark_finished_handler(transition, execution, user):
    pass


def mark_error_handler(transition, execution, user):
    pass
