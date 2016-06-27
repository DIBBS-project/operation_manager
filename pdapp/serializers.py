from rest_framework import serializers
from models import Execution
from django.contrib.auth.models import User


class ExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Execution
        fields = ('id', 'author', 'process_id', 'parameters', 'files', 'callback_url', 'output_location',
                  'creation_date', 'status', 'status_info', 'mrcluster_token')


class UserSerializer(serializers.ModelSerializer):
    executions = serializers.PrimaryKeyRelatedField(many=True, queryset=Execution.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'executions')
