# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task, group
from celery.utils.log import get_task_logger
from omapp.models import Execution
import threading

logger = get_task_logger("operation_manager")


@shared_task
def check_operations_periodically():
    print("checking executions")
    executions = Execution.objects.filter(ongoing_transition=False).all()
    executions = filter(lambda x: x.operation_state not in ["error", "finished"], executions)
    if len(executions) > 0:
        execution = executions[0]
        execution.ongoing_transition = True
        execution.save()
        process_execution_state.delay(execution.id)


@shared_task
def process_execution_state(execution_pk):
    print("checking execution %s" % (execution_pk))
    execution = Execution.objects.get(id=execution_pk)
    print(execution.operation_state)
    print(execution.get_operation_state_info())
    possible_transitions = filter(lambda x: x.to_state != "error", execution.get_operation_state_info().possible_transitions)
    print(possible_transitions)

    try:
        if len(possible_transitions) > 0:
            # Make the transition
            chosen_transition = possible_transitions[0]
            print("doing the transition to %s" % (chosen_transition.get_name()))
            execution.get_operation_state_info().make_transition(chosen_transition.get_name())
    except Exception as e:
        print(e)
        print("recovering an error")
        pass
    finally:
        execution.ongoing_transition = False
        execution.save()
