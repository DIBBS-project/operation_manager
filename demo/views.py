from django.shortcuts import render
import omapp.models as models
from omapp.or_client.apis import ProcessDefinitionsApi, ProcessImplementationsApi

from settings import Settings

import re
import json
import base64


def configure_basic_authentication(swagger_client, username, password):
    authentication_string = "%s:%s" % (username, password)
    base64_authentication_string = base64.b64encode(bytes(authentication_string))
    header_key = "Authorization"
    header_value = "Basic %s" % (base64_authentication_string, )
    swagger_client.api_client.default_headers[header_key] = header_value


# Index that provides a description of the API
def index(request):
    settings = Settings()
    urls = {
        'appliance_registry': re.sub('^https?://', '//', settings.appliance_registry_url),
        'operation_registry': re.sub('^https?://', '//', settings.operation_registry_url),
        'operation_manager': re.sub('^https?://', '//', settings.operation_manager_url),
        'resource_manager': re.sub('^https?://', '//', settings.resource_manager_url)
    }
    return render(request, "index.html", {'urls': urls})


def process_instances(request):

    # Configure a client for Operations
    operations_client = ProcessDefinitionsApi()
    operations_client.api_client.host = "%s" % (Settings.operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    tuples = []

    process_instances_list = models.ProcessInstance.objects.all()
    for process_instance in process_instances_list:
        process_def = operations_client.processdefs_id_get(id=process_instance.process_definition_id)
        process_instance.expanded_parameters = []
        for key, val in json.loads(process_instance.parameters).items():
            process_instance.expanded_parameters = process_instance.expanded_parameters + [{"key": key,
                                                                                            "val": val}]
        process_instance.expanded_files = []
        for key, val in json.loads(process_instance.files).items():
            process_instance.expanded_files = process_instance.expanded_files + [{"key": key,
                                                                                  "val": val}]
        exec_tuple = {
            "process_instance": process_instance,
            "process_definition": process_def,
        }
        tuples += [exec_tuple]

    return render(request, "process_instances.html", {"tuples": tuples})


def executions(request):
    executions_list = models.Execution.objects.all()

    # Configure a client for OperationVersions
    operation_versions_client = ProcessImplementationsApi()
    operation_versions_client.api_client.host = "%s" % (Settings.operation_registry_url,)
    configure_basic_authentication(operation_versions_client, "admin", "pass")

    # Configure a client for OperationDefinitions
    operations_client = ProcessDefinitionsApi()
    operations_client.api_client.host = "%s" % (Settings.operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    tuples = []
    for execution in executions_list:
        process_impl = operation_versions_client.processimpls_id_get(
            id=execution.process_instance.process_definition_id
        )
        process_def = operations_client.processdefs_id_get(id=process_impl.process_definition)
        all_tuple = {
            "execution": execution,
            "process_def": process_def,
        }
        tuples += [all_tuple]

    return render(request, "executions.html", {"executions": executions_list, "tuples": tuples})


def show_details(request, pk):

    execution = models.Execution.objects.filter(id=pk)[0]

    # Configure a client for OperationVersions
    operation_versions_client = ProcessImplementationsApi()
    operation_versions_client.api_client.host = "%s" % (Settings.operation_registry_url,)
    configure_basic_authentication(operation_versions_client, "admin", "pass")

    # Configure a client for OperationDefinitions
    operations_client = ProcessDefinitionsApi()
    operations_client.api_client.host = "%s" % (Settings.operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    process_impl = operation_versions_client.processimpls_id_get(id=execution.process_instance.process_definition_id)
    process_def = operations_client.processdefs_id_get(id=process_impl.process_definition)
    all_tuple = {
        "execution": execution,
        "process_impl": process_impl,
        "process_def": process_def,
        "appliance": process_impl.appliance,
    }

    return render(request, "tuple.html", {"tuple": all_tuple})


def create_process_instance(request):
    from omapp.or_client.apis.process_definitions_api import ProcessDefinitionsApi

    # Configure a client for OperationDefinitions
    operations_client = ProcessDefinitionsApi()
    operations_client.api_client.host = "%s" % (Settings.operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    processdefs = operations_client.processdefs_get()
    return render(request, "process_instance_form.html", {"processdefs": processdefs})


def create_execution(request):
    return render(request, "execution_form.html", {"instances": models.ProcessInstance.objects.all()})
