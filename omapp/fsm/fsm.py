from django_states.fields import StateField
from django_states.machine import StateMachine, StateDefinition, StateTransition
from django_states.models import StateModel
from omapp.core import mark_deploying_handler
from omapp.core import mark_bootstrapping_handler
from omapp.core import mark_configuring_handler
from omapp.core import mark_executing_handler
from omapp.core import mark_collecting_handler
from omapp.core import mark_finishing_handler
from omapp.core import mark_error_handler
import logging


class ExecutionStateMachine(StateMachine):
    log_transitions = True

    # possible states
    class initiated(StateDefinition):
        description = 'Execution initiated'
        initial = True

    class deployed(StateDefinition):
        description = 'Execution deployed'

    class bootstrapped(StateDefinition):
        description = 'Execution bootstrapped'

    class configured(StateDefinition):
        description = 'Execution configured'

    class executed(StateDefinition):
        description = 'Execution executed'

    class collected(StateDefinition):
        description = 'Execution collected'

    class finished(StateDefinition):
        description = 'Execution finished'

    class error(StateDefinition):
        description = 'Execution error'

    # state transitions
    class mark_deploying(StateTransition):
        from_state = 'initiated'
        to_state = 'deployed'
        description = 'Deploy the execution dependencies'

        def handler(transition, instance, user):
            logging.info("INITIATED => DEPLOYING")
            mark_deploying_handler(transition, instance, user)

    class mark_bootstrapping(StateTransition):
        from_state = 'deployed'
        to_state = 'bootstrapped'
        description = 'Bootstrap the execution of the operation'

        def handler(transition, instance, user):
            logging.info("DEPLOYING => BOOTSTRAPPED")
            mark_bootstrapping_handler(transition, instance, user)

    class mark_configuring(StateTransition):
        from_state = 'bootstrapped'
        to_state = 'configured'
        description = 'Configure the execution of the operation'

        def handler(transition, instance, user):
            logging.info("BOOTSTRAPPED => CONFIGURED")
            mark_configuring_handler(transition, instance, user)

    class mark_executing(StateTransition):
        from_state = 'configured'
        to_state = 'executed'
        description = 'Execute the operation'

        def handler(transition, instance, user):
            logging.info("CONFIGURED => EXECUTED")
            mark_executing_handler(transition, instance, user)

    class mark_collecting(StateTransition):
        from_state = 'executed'
        to_state = 'collected'
        description = 'Post execution'

        def handler(transition, instance, user):
            logging.info("EXECUTED => COLLECTED")
            mark_collecting_handler(transition, instance, user)

    class mark_finishing(StateTransition):
        from_state = 'collected'
        to_state = 'finished'
        description = 'Finished the execution of the operation'

        def handler(transition, instance, user):
            logging.info("COLLECTED => FINISHED")
            mark_finishing_handler(transition, instance, user)

    class mark_error(StateTransition):
        from_states = ('initiated', 'deployed', 'bootstrapped', 'configured', 'executed',
                       'collected', 'finished')
        to_state = 'error'
        description = 'Put the execution of the operation in error state'

        def handler(transition, instance, user):
            logging.info("* => ERROR")
            mark_error_handler(transition, instance, user)
