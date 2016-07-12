from django.shortcuts import render
import pdapp.models as models
from pdapp.pr_client.apis import ProcessDefinitionsApi, ProcessImplementationApi

from settings import Settings

import re


def get_appliance(appliance_id):
    return {
        "name": "Hadoop",
        "infrastructure": "Chameleon (OpenStack)"
    }


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


# Index that provides a description of the API
def executions(request):

    tuples = []

    executions = models.Execution.objects.all()
    for execution in executions:
        process_impl = ProcessImplementationApi().processimpls_id_get(id=execution.process_id)
        process_def = ProcessDefinitionsApi().processdefs_id_get(id=process_impl.process_definition)
        tuple = {
            "execution": execution,
            "process_impl": process_impl,
            "process_def": process_def,
            "appliance": get_appliance(process_impl.appliance)
        }
        tuples += [tuple]

    return render(request, "executions.html", {"tuples": tuples})


def show_details(request, pk):

    execution = models.Execution.objects.filter(id=pk)[0]
    process_impl = ProcessImplementationApi().processimpls_id_get(id=execution.process_id)
    process_def = ProcessDefinitionsApi().processdefs_id_get(id=process_impl.process_definition)
    tuple = {
        "execution": execution,
        "process_impl": process_impl,
        "process_def": process_def,
        "appliance": get_appliance(process_impl.appliance)
    }

    return render(request, "tuple.html", {"tuple": tuple})


def create_execution(request):
    from pdapp.pr_client.apis.process_definitions_api import ProcessDefinitionsApi
    processdefs = ProcessDefinitionsApi().processdefs_get()
    return render(request, "exec_form.html", {"processdefs": processdefs})
