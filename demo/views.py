from django.shortcuts import render
import pdapp.models as models
from pdapp.pr_client.apis import ProcessDefinitionsApi, ProcessImplementationApi

from settings import Settings

import re, json


# Index that provides a description of the API
def index(request):
    settings = Settings()
    urls = {
        'appliance_registry': re.sub('^https?://', '//', settings.appliance_registry_url),
        'process_registry': re.sub('^https?://', '//', settings.process_registry_url),
        'process_dispatcher': re.sub('^https?://', '//', settings.process_dispatcher_url),
        'resource_provisioner': re.sub('^https?://', '//', settings.resource_provisioner_url)
    }
    return render(request, "index.html", {'urls': urls})


def process_instances(request):

    tuples = []

    process_instances_list = models.ProcessInstance.objects.all()
    for process_instance in process_instances_list:
        process_def = ProcessDefinitionsApi().processdefs_id_get(id=process_instance.process_definition_id)
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

    tuples = []
    for execution in executions_list:
        process_impl = ProcessImplementationApi().processimpls_id_get(id=execution.process_instance.process_definition_id)
        process_def = ProcessDefinitionsApi().processdefs_id_get(id=process_impl.process_definition)
        tuple = {
            "execution": execution,
            "process_impl": process_impl,
            "process_def": process_def,
        }
        tuples += [tuple]

    return render(request, "executions.html", {"executions": executions_list, "tuples": tuples})


def show_details(request, pk):

    execution = models.Execution.objects.filter(id=pk)[0]
    process_impl = ProcessImplementationApi().processimpls_id_get(id=execution.process_instance.process_definition_id)
    process_def = ProcessDefinitionsApi().processdefs_id_get(id=process_impl.process_definition)
    tuple = {
        "execution": execution,
        "process_impl": process_impl,
        "process_def": process_def,
        "appliance": process_impl.appliance,
    }

    return render(request, "tuple.html", {"tuple": tuple})


def create_process_instance(request):
    from pdapp.pr_client.apis.process_definitions_api import ProcessDefinitionsApi
    processdefs = ProcessDefinitionsApi().processdefs_get()
    return render(request, "process_instance_form.html", {"processdefs": processdefs})


def create_execution(request):
    return render(request, "execution_form.html", {"instances": models.ProcessInstance.objects.all()})
