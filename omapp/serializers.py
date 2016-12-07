from rest_framework import serializers
from models import Instance, Execution
from django.contrib.auth.models import User


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
                  'resource_provisioner_token',
                  'resource_manager_agent_credentials',
                  'operation_manager_agent_credentials',
                  'output_location',
                  'hints')


class UserSerializer(serializers.ModelSerializer):
    executions = serializers.PrimaryKeyRelatedField(many=True, queryset=Execution.objects.all())
    operation_instances = serializers.PrimaryKeyRelatedField(many=True, queryset=Instance.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'executions', 'operation_instances')
