# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.db import models
from django_states.fields import StateField
from django_states.models import StateModel
from jsonfield import JSONField

from .fsm.fsm import ExecutionStateMachine


class Instance(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='operation_instances', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, default='')
    process_definition_id = models.IntegerField()
    parameters = JSONField()
    files = JSONField()
    creation_date = models.DateTimeField(auto_now_add=True)


class Execution(StateModel):
    operation_state = StateField(machine=ExecutionStateMachine, default='initiated')

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='executions', on_delete=models.CASCADE)
    operation_instance = models.ForeignKey(Instance, related_name='executions', on_delete=models.CASCADE)
    callback_url = models.CharField(max_length=2048, blank=True, default='')
    force_spawn_cluster = models.CharField(max_length=8, blank=True, default='')
    creation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2048, blank=True, default='NEW')
    status_info = models.CharField(max_length=2048, blank=True, default='')
    output_location = models.CharField(max_length=2048, blank=True, default='')
    hints = models.CharField(max_length=2048, blank=True, default='{}')
    cluster_id = models.IntegerField(default=-1)
    resource_manager_agent_credentials = models.CharField(max_length=2048, blank=True, default='{}')
    operation_manager_agent_credentials = models.CharField(max_length=2048, blank=True, default='{}')

    ongoing_transition = models.BooleanField(default=False)
