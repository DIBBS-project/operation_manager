# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import logging

from django_states.fields import StateField
from django_states.machine import StateDefinition, StateMachine, StateTransition
from django_states.models import StateModel

from omapp import core

logger = logging.getLogger(__name__)


class EUArticle45Mixin(object):
    """
    "Freedom of movement for workers shall be secured within the Community."
        - Article 45 of the Treaty on the Functioning of the European Union

    Basically just let whoever command a state transition. I'm so clever at
    naming things.
    """
    @classmethod
    def has_permission(cls, instance, user):
        return True


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
    class mark_deploying(EUArticle45Mixin, StateTransition):
        from_state = 'initiated'
        to_state = 'deployed'
        description = 'Deploy the execution dependencies'

        def handler(transition, instance, user):
            logger.info("INITIATED => DEPLOYING")
            core.mark_deploying_handler(transition, instance, user)

    class mark_bootstrapping(EUArticle45Mixin, StateTransition):
        from_state = 'deployed'
        to_state = 'bootstrapped'
        description = 'Bootstrap the execution of the operation'

        def handler(transition, instance, user):
            logger.info("DEPLOYING => BOOTSTRAPPED")
            core.mark_bootstrapping_handler(transition, instance, user)

    class mark_configuring(EUArticle45Mixin, StateTransition):
        from_state = 'bootstrapped'
        to_state = 'configured'
        description = 'Configure the execution of the operation'

        def handler(transition, instance, user):
            logger.info("BOOTSTRAPPED => CONFIGURED")
            core.mark_configuring_handler(transition, instance, user)

    class mark_executing(EUArticle45Mixin, StateTransition):
        from_state = 'configured'
        to_state = 'executed'
        description = 'Execute the operation'

        def handler(transition, instance, user):
            logger.info("CONFIGURED => EXECUTED")
            core.mark_executing_handler(transition, instance, user)

    class mark_collecting(EUArticle45Mixin, StateTransition):
        from_state = 'executed'
        to_state = 'collected'
        description = 'Post execution'

        def handler(transition, instance, user):
            logger.info("EXECUTED => COLLECTED")
            core.mark_collecting_handler(transition, instance, user)

    class mark_finishing(EUArticle45Mixin, StateTransition):
        from_state = 'collected'
        to_state = 'finished'
        description = 'Finished the execution of the operation'

        def handler(transition, instance, user):
            logger.info("COLLECTED => FINISHED")
            core.mark_finishing_handler(transition, instance, user)

    class mark_error(EUArticle45Mixin, StateTransition):
        from_states = ('initiated', 'deployed', 'bootstrapped', 'configured', 'executed',
                       'collected', 'finished')
        to_state = 'error'
        description = 'Put the execution of the operation in error state'

        def handler(transition, instance, user):
            logger.info("* => ERROR")
            core.mark_error_handler(transition, instance, user)
