from rest_framework import serializers
from models import ProcessInstance, Execution
from django.contrib.auth.models import User


class ProcessInstanceSerializer(serializers.ModelSerializer):
    executions = serializers.PrimaryKeyRelatedField(many=True, queryset=Execution.objects.all())

    class Meta:
        model = ProcessInstance
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
                  'process_instance',
                  'callback_url',
                  'force_spawn_cluster',
                  'creation_date',
                  'status',
                  'status_info',
                  'resource_provisioner_token',
                  'output_location')


class UserSerializer(serializers.ModelSerializer):
    executions = serializers.PrimaryKeyRelatedField(many=True, queryset=Execution.objects.all())
    process_instances = serializers.PrimaryKeyRelatedField(many=True, queryset=ProcessInstance.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'executions', 'process_instances')
