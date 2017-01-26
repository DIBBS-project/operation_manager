# coding: utf-8
from __future__ import absolute_import, print_function

import re
import json

from django.conf import settings
from django.shortcuts import render

from common_dibbs.clients.or_client.apis import OperationsApi, OperationVersionsApi
from common_dibbs.clients.or_client.apis.operations_api import OperationsApi
from common_dibbs.django import relay_swagger


import omapp.models as models


# Index that provides a description of the API
def index(request):
    urls = {
        'appliance_registry': re.sub('^https?://', '//', settings.DIBBS['urls']['ar']),
        'operation_registry': re.sub('^https?://', '//', settings.DIBBS['urls']['or']),
        'operation_manager': re.sub('^https?://', '//', settings.DIBBS['urls']['om']),
        'resource_manager': re.sub('^https?://', '//', settings.DIBBS['urls']['rm'])
    }
    return render(request, "index.html", {'urls': urls})


def operation_instances(request):
    # Configure a client for Operations
    operations_client = OperationsApi()
    operations_client.api_client.host = settings.DIBBS['urls']['or']
    relay_swagger(operations_client, request)

    tuples = []

    operation_instances_list = models.Instance.objects.all()
    for operation_instance in operation_instances_list:
        process_def = operations_client.processdefs_id_get(id=operation_instance.process_definition_id)
        operation_instance.expanded_parameters = []
        for key, val in json.loads(operation_instance.parameters).items():
            operation_instance.expanded_parameters = operation_instance.expanded_parameters + [{"key": key,
                                                                                            "val": val}]
        operation_instance.expanded_files = []
        for key, val in json.loads(operation_instance.files).items():
            operation_instance.expanded_files = operation_instance.expanded_files + [{"key": key,
                                                                                  "val": val}]
        exec_tuple = {
            "operation_instance": operation_instance,
            "process_definition": process_def,
        }
        tuples += [exec_tuple]

    return render(request, "operation_instances.html", {"tuples": tuples})


def executions(request):
    executions_list = models.Execution.objects.all()

    # Configure a client for OperationVersions
    operation_versions_client = ProcessImplementationsApi()
    operation_versions_client.api_client.host = settings.DIBBS['urls']['or']
    relay_swagger(operation_versions_client, request)

    # Configure a client for OperationDefinitions
    operations_client = OperationsApi()
    operations_client.api_client.host = settings.DIBBS['urls']['or']
    relay_swagger(operations_client, request)

    tuples = []
    for execution in executions_list:
        process_impl = operation_versions_client.processimpls_id_get(
            id=execution.operation_instance.process_definition_id
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
    operation_versions_client.api_client.host = settings.DIBBS['urls']['or']
    relay_swagger(operation_versions_client, request)

    # Configure a client for OperationDefinitions
    operations_client = OperationsApi()
    operations_client.api_client.host = settings.DIBBS['urls']['or']
    relay_swagger(operations_client, request)

    process_impl = operation_versions_client.processimpls_id_get(id=execution.operation_instance.process_definition_id)
    process_def = operations_client.processdefs_id_get(id=process_impl.process_definition)
    all_tuple = {
        "execution": execution,
        "process_impl": process_impl,
        "process_def": process_def,
        "appliance": process_impl.appliance,
    }

    return render(request, "tuple.html", {"tuple": all_tuple})


def create_operation_instance(request):
    # Configure a client for OperationDefinitions
    operations_client = OperationsApi()
    operations_client.api_client.host = settings.DIBBS['urls']['or']
    relay_swagger(operations_client, request)

    processdefs = operations_client.processdefs_get()
    return render(request, "operation_instance_form.html", {"processdefs": processdefs})


def create_execution(request):
    return render(request, "execution_form.html", {"instances": models.Instance.objects.all()})
