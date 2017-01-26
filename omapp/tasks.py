# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import traceback

from celery import shared_task
from celery.utils.log import get_task_logger

from .models import Execution

logger = get_task_logger("operation_manager")


@shared_task
def check_operations_periodically():
    # print("checking executions")
    executions = Execution.objects.filter(ongoing_transition=False).all()
    executions = filter(lambda x: x.operation_state not in ["error", "finished"], executions)
    # exections = [e for e in executions if e.operation_state not in [...]]
    if len(executions) > 0:
        execution = executions[0]
        execution.ongoing_transition = True
        execution.save()
        process_execution_state.delay(execution.id)


@shared_task
def process_execution_state(execution_pk):
    execution = Execution.objects.get(id=execution_pk)
    # possible_transitions = filter(lambda x: x.to_state != "error", execution.get_operation_state_info().possible_transitions)
    state_info = execution.get_operation_state_info()

    possible_transitions = [t for t in state_info.possible_transitions if t.to_state != 'error']

    print("Execution '{}' is in state '{}', can go to {}".format(
        execution_pk, execution.operation_state,
        [t.get_name() for t in possible_transitions],
    ))

    try:
        if len(possible_transitions) > 0:
            # Make a transition
            chosen_transition = possible_transitions[0]
            print("Commanding transition of execution '{}' to '{}'".format(
                execution_pk, chosen_transition.get_name(),
            ))
            state_info.make_transition(chosen_transition.get_name(), user=execution.author)
    except Exception as e:
        print(traceback.format_exc())
    finally:
        execution.ongoing_transition = False
        execution.save()
