from django.db import models
from django.contrib.auth.models import User


from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from jsonfield import JSONField

# Create your models here.


class Instance(models.Model):
    author = models.ForeignKey('auth.User', related_name='operation_instances', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, default='')
    process_definition_id = models.IntegerField()
    parameters = JSONField()
    files = JSONField()
    creation_date = models.DateTimeField(auto_now_add=True)


class Execution(models.Model):
    author = models.ForeignKey('auth.User', related_name='executions', on_delete=models.CASCADE)
    operation_instance = models.ForeignKey(Instance, related_name='executions', on_delete=models.CASCADE)
    callback_url = models.CharField(max_length=2048, blank=True, default='')
    force_spawn_cluster = models.CharField(max_length=8, blank=True, default='')
    creation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2048, blank=True, default='NEW')
    status_info = models.CharField(max_length=2048, blank=True, default='')
    resource_provisioner_token = models.CharField(max_length=128)
    output_location = models.CharField(max_length=2048, blank=True, default='')
    hints = models.CharField(max_length=2048, blank=True, default='{}')


# Add a token upon user creation
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(author=instance)
