# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Execution, Instance


class InstanceSerializer(serializers.ModelSerializer):
    executions = serializers.PrimaryKeyRelatedField(many=True, queryset=Execution.objects.all())

    class Meta:
        model = Instance
        fields = ('id',
                  'author',
                  'name',
                  'process_definition_id',
                  'parameters',
                  'files',
                  'creation_date',
                  'executions')


class ExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Execution
        fields = ('id',
                  'author',
                  'operation_instance',
                  'callback_url',
                  'force_spawn_cluster',
                  'creation_date',
                  'status',
                  'status_info',
                  'resource_manager_agent_credentials',
                  'operation_manager_agent_credentials',
                  'output_location',
                  'hints',
                  'operation_state')


class UserSerializer(serializers.ModelSerializer):
    executions = serializers.PrimaryKeyRelatedField(many=True, queryset=Execution.objects.all())
    operation_instances = serializers.PrimaryKeyRelatedField(many=True, queryset=Instance.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'executions', 'operation_instances')
