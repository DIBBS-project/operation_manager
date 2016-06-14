from django.shortcuts import render
import pdapp.models as models
from pdapp.prapp_client.apis import ProcessDefinitionsApi


def get_appliance(appliance_id):
    return {
        "name": "Hadoop",
        "infrastructure": "Chameleon (OpenStack)"
    }


# Index that provides a description of the API
def index(request):

    tuples = []

    executions = models.Execution.objects.all()
    for execution in executions:
        ret = ProcessDefinitionsApi().processdef_id_get(id=execution.process_id)
        tuple = {
            "execution": execution,
            "process": ret,
            "appliance": get_appliance(ret.appliance_id)
        }
        tuples += [tuple]

    return render(request, "index.html", {"tuples": tuples})


def show_details(request, pk):

    execution = models.Execution.objects.filter(id=pk)[0]
    ret = ProcessDefinitionsApi().processdef_id_get(id=execution.process_id)
    tuple = {
        "execution": execution,
        "process": ret,
        "appliance": get_appliance(ret.appliance_id)
    }

    return render(request, "tuple.html", {"tuple": tuple})


def create_execution(request):
    return render(request, "exec_form.html")
