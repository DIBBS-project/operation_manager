from django_states.fields import StateField
from django_states.machine import StateMachine, StateDefinition, StateTransition
from django_states.models import StateModel
from omapp.core import mark_deploying_handler, mark_ready_to_run_handler, mark_running_handler, mark_executed_handler, mark_finished_handler, mark_error_handler
import logging


class ExecutionStateMachine(StateMachine):
    log_transitions = True

    # possible states
    class initiated(StateDefinition):
        description = 'Execution initiated'
        initial = True

    class deploying(StateDefinition):
        description = 'Execution deploying'

    class ready_to_run(StateDefinition):
        description = 'Execution ready_to_run'

    class running(StateDefinition):
        description = 'Execution running'

    class executed(StateDefinition):
        description = 'Execution executed'

    class finished(StateDefinition):
        description = 'Execution finished'

    class error(StateDefinition):
        description = 'Execution error'

    # state transitions
    class mark_deploying(StateTransition):
        from_state = 'initiated'
        to_state = 'deploying'
        description = 'Deploy the execution dependencies'

        def handler(transition, instance, user):
            logging.info("INITIATED => DEPLOYING")
            mark_deploying_handler(transition, instance, user)

    class mark_ready_to_run(StateTransition):
        from_state = 'deploying'
        to_state = 'ready_to_run'
        description = 'The execution of the operation is ready to launch'

        def handler(transition, instance, user):
            logging.info("DEPLOYING => ready_to_run")
            mark_ready_to_run_handler(transition, instance, user)

    class mark_running(StateTransition):
        from_state = 'ready_to_run'
        to_state = 'running'
        description = 'The execution of the operation is running'

        def handler(transition, instance, user):
            logging.info("ready_to_run => RUNNING")
            mark_running_handler(transition, instance, user)

    class mark_executed(StateTransition):
        from_state = 'running'
        to_state = 'executed'
        description = 'Post execution'

        def handler(transition, instance, user):
            logging.info("RUNNING => EXECUTED")
            mark_executed_handler(transition, instance, user)

    class mark_finished(StateTransition):
        from_state = 'executed'
        to_state = 'finished'
        description = 'Finished the execution of the operation'

        def handler(transition, instance, user):
            logging.info("EXECUTED => FINISHED")
            mark_finished_handler(transition, instance, user)

    class mark_error(StateTransition):
        from_states = ('initiated', 'deploying', 'ready_to_run', 'running', 'executed', 'finished')
        to_state = 'error'
        description = 'Put the execution of the operation in error state'

        def handler(transition, instance, user):
            logging.info("* => ERROR")
            mark_error_handler(transition, instance, user)
