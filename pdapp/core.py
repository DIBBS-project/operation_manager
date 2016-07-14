import requests, os
import json
import uuid
import logging


def deploy_cluster(execution, appliance, resource_provisioner_url):

    headers = {
        "TOKEN": execution.resource_provisioner_token
    }

    execution.status = "DEPLOYING"
    execution.status_info = "Creating virtual cluster"
    execution.save()

    logging.info("creating the logical cluster")
    cluster_creation_data = {"user_id": "1",
                             "appliance": appliance,
                             "name": "MyHadoopCluster"}
    r = requests.post('%s/clusters/' % resource_provisioner_url,
                      data=json.dumps(cluster_creation_data), headers=headers)

    response = json.loads(r.content)
    cluster_id = response["cluster_id"]

    # Add a master node to the cluster
    execution.status_info = "Adding master node"
    execution.save()

    logging.info("adding a new node (master) to the cluster %s" % (cluster_id))
    node_addition_data = {"cluster_id": cluster_id}
    r = requests.post('%s/hosts/' % resource_provisioner_url,
                      data=json.dumps(node_addition_data), headers=headers)

    # Add a slave node to the cluster
    execution.status_info = "Adding slave node"
    execution.save()

    logging.info("adding a new node (slave) to the cluster %s" % (cluster_id))
    r = requests.post('%s/hosts/' % resource_provisioner_url,
                      data=json.dumps(node_addition_data), headers=headers)

    execution.status = "DEPLOYED"
    execution.status_info = ""
    execution.save()

    # Get the cluster description
    logging.info("get a description of the cluster %s" % cluster_id)
    r = requests.get('%s/clusters/%s/' % (resource_provisioner_url, cluster_id), headers=headers)
    description = json.loads(r.content)

    logging.info("description will be returned %s" % description)
    return description


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
    logging.info("generated script in %s" % script_path)

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
    print (r)

    execution.status = "RUNNING"
    execution.status_info = "Executing the job"
    execution.save()

    # Run "test.sh" with bash
    logging.info("running script.sh")
    r = requests.get('%s/fs/run/script.sh/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
    # curl --header "token: $TOKEN" -i -X GET  $REMOTE_HADOOP_WEBSERVICE_HOST/fs/run/test.sh/
    print (r)

    # Download the "output.txt" file
    execution.status = "COLLECTING"
    execution.status_info = "Getting output file"
    execution.save()

    logging.info("downloading the output")
    r = requests.get('%s/fs/download/output.txt/' % (REMOTE_HADOOP_WEBSERVICE_HOST), headers=headers)
    # curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/download/out.txt/
    print (r)

    # Sending the result to the callback url
    if callback_url:
        logging.info("calling the callback (%s)" % callback_url)
        execution.status_info = "Sending output to %s" % (callback_url)
        execution.save()

        r = requests.post(callback_url, data=r.content)
        print (r)

    execution.output_location = '%s/fs/download/output.txt/?token=%s' % (REMOTE_HADOOP_WEBSERVICE_HOST, token)
    execution.status = "FINISHED"
    execution.status_info = ""
    execution.save()

    return True
