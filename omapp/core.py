# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging
import os
import re
import sys
import thread
import time
import traceback
import uuid

import requests
from common_dibbs.clients.rm_client.rest import ApiException as RmApiException
from common_dibbs.misc import configure_basic_authentication
from requests.exceptions import ConnectionError
from rest_framework import status
from rest_framework.response import Response

from . import clients
from .process_record import set_variables, set_files, fileneames_dictionary, get_bash_script
from .sched.scheduling_policies import DummySchedulingPolicy as SchedulingPolicy

# def getattrkey(obj, attrkey):
#     try:
#         value = obj[attrkey]
#     except (KeyError, AttributeError):
#         value = getattr(obj, attrkey)
#
#     return value


def filter_clusters_in_site(clusters, hints):
    all_credentials = clients.credentials.credentials_get()

    # Find the sites that can be used by the used (i.e. sites where user has credentials)
    sites = []
    credentials = hints["credentials"]
    for credential in credentials:
        # Filter credentials that corresponds to the name provided in the hints
        matching_credentials = filter(lambda cred: cred.name == credential, all_credentials)
        if len(matching_credentials) == 0:
            continue
        # Use the first credential that has been found
        matching_credential = matching_credentials[0]
        if matching_credential.site_name not in sites:
            sites += [matching_credential.site_name]

    # Find clusters that are in sites that the user can use
    results = []
    for cluster in clusters:
        if cluster.appliance_impl == "":
            continue
        appliance_impl = clients.appliance_implementations.appliances_impl_name_get(cluster.appliance_impl)
        # Detect the site of the cluster (Site <--> ApplianceImpl <--> Cluster)
        if appliance_impl.site in sites or "*" in credentials:
            results += [cluster]
    return results


def deploy_cluster(execution, appliance, hints=None):
    execution.status = "DEPLOYING"
    execution.status_info = "Creating virtual cluster"
    execution.save()

    # Determine the number of slaves that the new cluster should contain
    hints = json.loads(execution.hints)
    targeted_slaves_count = 2
    if "slave_nodes_count" in hints:
        targeted_slaves_count = hints["slave_nodes_count"]

    logging.info("creating the logical cluster")
    cluster_creation_data = {
        "user_id": "1",  # TODO: Remove (update the swagger client to >= 0.1.11 first)
        "appliance": appliance,
        "name": "MyHadoopCluster",
        "targeted_slaves_count": targeted_slaves_count
    }

    if hints is not None:
        cluster_creation_data["hints"] = json.dumps(hints)

    # HINT INSERTION: Add a hint to this function to help to chose the right site
    response = clients.clusters.clusters_post(data=cluster_creation_data)
    cluster_id = response.id

    execution.status = "DEPLOYED"
    execution.status_info = ""
    execution.save()

    # Get the cluster description
    logging.info("get a description of the cluster %s" % cluster_id)
    description = clients.clusters.clusters_id_get(id=cluster_id)

    logging.info("description will be returned %s" % description)
    return description


def create_temporary_user(cluster, execution):
    cluster_id = cluster.id if not isinstance(cluster, dict) else cluster["id"]

    execution.status = "PREPARING"
    execution.status_info = ""
    execution.save()

    logging.info("creating a temporary user on cluster %s" % (cluster.name,))

    execution.status_info = "Creating a temporary user on cluster %s" % (cluster.name,)
    execution.save()

    credentials = clients.clusters.clusters_id_new_account_post(cluster_id).to_dict()
    execution.resource_manager_credentials = json.dumps(credentials)

    execution.status_info = "Temporary user created"
    execution.save()

    return credentials


def run_process(cluster, script, callback_url, execution, credentials):
    master_node_ip = cluster.master_node_ip if not isinstance(cluster, dict) else cluster["master_node_ip"]

    # Create a client for Operations
    ops_client = OpsApi()
    ops_client.api_client.host = "http://%s:8011" % (master_node_ip,)

    username = credentials.username if not isinstance(credentials, dict) else credentials["username"]
    password = credentials.password if not isinstance(credentials, dict) else credentials["password"]

    configure_basic_authentication(ops_client, username, password)

    # Create an operation, and post it to the Operation Manager Agent running on port 8011 on the
    # master node
    ops_data = {
        "script": script,
        "callback_url": callback_url
    }

    logging.info("creation the operation %s" % (ops_data,))
    execution.status_info = "Creating the Operation"
    execution.save()

    result = ops_client.ops_post(data=ops_data)

    # Save information about the operation's execution in database. Detect if an issue happened.
    if not hasattr(result, "id"):
        msg = "Could not create operation (%s) on the master node (%s)" % (ops_data, master_node_ip)
        logging.error("%s, aborting..." % (msg, master_node_ip))
        execution.status = "ERROR"
        execution.status_info = "%s" % (msg, )
        execution.save()
        raise Exception(msg)
    else:
        # Save temporary credentials information in the operation
        credentials_dict = {
            "username": username,
            "password": password
        }
        credentials_json = json.dumps(credentials_dict)
        execution.operation_manager_agent_credentials = credentials_json
        execution.save()

    operation = result

    logging.info("running the operation %s" % (ops_data,))
    execution.status = "RUNNING"
    execution.status_info = "Executing the operation (%s on %s)" % (operation.id, master_node_ip)
    execution.save()

    ops_client.ops_id_run_op_post(operation.id)

    return True


def mark_deploying_handler(transition, execution, user):
    try:
        execution.status = "INIT"
        execution.status_info = "Checking parameters"
        execution.save()

        # Check that the process definition exists
        operation_instance = execution.operation_instance
        operation = clients.operations.operations_id_get(id=operation_instance.process_definition_id)

        operation_version_id = operation.implementations[0]
        operation_version = clients.operation_versions.operationversions_id_get(id=operation_version_id)

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
        clusters = clients.clusters.clusters_get()
        hints = None
        if execution.hints != "{}":
            hints = json.loads(execution.hints)
            clusters = filter_clusters_in_site(clusters, hints)
        # HINT INSERTION: Here we could use hints to select the right cluster
        cluster_to_use = SchedulingPolicy().decide_cluster_deployment(appliance, clusters, force_new=execution.force_spawn_cluster!='', hints=hints)
        if cluster_to_use is None:
            logging.info("Creating a virtual cluster")
            cluster_to_use = deploy_cluster(execution, appliance, hints=hints)
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


def mark_bootstrapping_handler(transition, execution, user):
    clusters = clients.clusters.clusters_get()
    cluster_to_use = filter(lambda c: c.id == execution.cluster_id, clusters)[0]

    retry_count = 0
    max_retry = 100
    credentials = None
    while not credentials and retry_count < max_retry:
        try:
            logging.info("Creating a temporary user on the cluster %s" % cluster_to_use)
            credentials = create_temporary_user(cluster_to_use, execution)
            credentials_json = json.dumps(credentials)
            execution.resource_manager_agent_credentials = credentials_json
            execution.save()
        except (ConnectionError, RmApiException):
            execution.status_info = "The cluster is still bootstrapping... waiting for it to be ready (attempt: %s/%s)" % (retry_count, max_retry)
            execution.save()
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
    pass


def mark_configuring_handler(transition, execution, user):
    # Check that the process definition exists
    operation_instance = execution.operation_instance
    operation = clients.operations.operations_id_get(id=operation_instance.process_definition_id)

    # FIXME: the chosen process implementation is always the first one
    # UPDATE: New architecture: No process implementation but process version, it will be fixed when changing this
    operation_version_id = operation.implementations[0]
    operation_version = clients.operation_versions.operationversions_id_get(id=operation_version_id)

    # Prevent the operation manager to crash if the user provided an empty non JSON output
    # parameter
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


def mark_executing_handler(transition, execution, user):
    try:
        # Check that the process definition exists
        operation_instance = execution.operation_instance
        operation = clients.operations.operations_id_get(id=operation_instance.process_definition_id)

        # FIXME: the chosen process implementation is always the first one
        # UPDATE: New architecture: No process implementation but process version, it will be fixed when changing this
        operation_version_id = operation.implementations[0]
        operation_version = clients.operation_versions.operationversions_id_get(id=operation_version_id)

        if operation_version.output_parameters == "":
            operation_version.output_parameters = {}
        else:
            operation_version.output_parameters = json.loads(operation_version.output_parameters)
        #
        # Get all the required information
        parameters = json.loads(execution.operation_instance.parameters)
        files = json.loads(execution.operation_instance.files)

        filenames = fileneames_dictionary(files)
        set_variables(operation_version, parameters)
        set_files(operation_version, filenames)

        script = get_bash_script(operation_version, files, filenames)
        callback_url = execution.callback_url

        clusters = clients.clusters.clusters_get()
        cluster_to_use = filter(lambda c: c.id == execution.cluster_id, clusters)[0]

        credentials_unicode = execution.resource_manager_agent_credentials
        credentials = json.loads(credentials_unicode)

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


def mark_collecting_handler(transition, execution, user):
    if execution.status == "FAILED":
        return

    # Download the "output.txt" file
    execution.status = "COLLECTING"
    execution.status_info = "Getting output file"
    execution.save()

    # Check that the process definition exists
    operation_version = clients.operation_versions.operationversions_id_get(id=execution.operation_instance_id)
    output_file_path = None
    output_file_name = None
    if operation_version.output_type == "file":
        cluster = clients.clusters.clusters_id_get(execution.cluster_id)
        logging.info("I will process the output of this execution by using these credentials %s" % (execution.operation_manager_agent_credentials))
        output_parameters = json.loads(operation_version.output_parameters)
        output_file_name = output_parameters.get("file_path", None)
        if output_file_name is not None:
            # Get a token to the remote cluster
            operation_manager_agent_credentials = json.loads(execution.operation_manager_agent_credentials)
            headers = {
                "username": operation_manager_agent_credentials["username"],
                "password": operation_manager_agent_credentials["password"]
            }
            r = requests.get('http://%s:8011/ops/%s/get_tmp_password/' % (cluster.master_node_ip, headers["username"]), headers=headers)
            temporary_password = r.json()["tmp_password"]

            # Generate a token to work with the deployed appliance
            headers = {
                "username": operation_manager_agent_credentials["username"],
                "password": temporary_password
            }
            r = requests.get('http://%s:8000/generate_new_token/' % (cluster.master_node_ip), headers=headers)
            print (r)
            token = r.json()["token"]

            # Downloads the output
            headers = {
                "token": token
            }

            download_url = 'http://%s:8000/fs/download/%s/' % (cluster.master_node_ip, output_file_name)
            r = requests.get(download_url, headers=headers)
            execution.output_location = "%s?token=%s" % (download_url, token)
            execution.save()

            # Write the downloaded file in a temporary file
            output_file_path = "/tmp/%s" % (uuid.uuid4())
            with open(output_file_path, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)
        else:
            logging.error("Could not understand where is the output file (execution.id=%s)" % (execution.id))
    else:
        logging.error("Could not understand the output format(execution.id=%s): '%s'" % (execution.id, operation_version.output_type))

    # Sending the result to the callback url
    if execution.callback_url:
        logging.info("calling the callback (%s)" % execution.callback_url)
        execution.status_info = "Sending output to %s" % (execution.callback_url)
        execution.save()

        if output_file_path:
            files = {'file': (output_file_name, open(output_file_path, 'rb'))}
            r = requests.post(execution.callback_url, files=files)
        else:
            r = requests.post(execution.callback_url, data={"finished": True})
        logging.info("made a request on %s (%s)" % (execution.callback_url, r))

    return True


def mark_finishing_handler(transition, execution, user):
    execution.status = "FINISHED"
    execution.status_info = ""
    execution.save()

    return True


def mark_error_handler(transition, execution, user):
    execution.status = "ERROR"
    execution.save()

    return True
