from django.db import models
from django.contrib.auth.models import User


from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from jsonfield import JSONField

# Create your models here.


class Execution(models.Model):
    author = models.ForeignKey('auth.User', related_name='executions')
    process_id = models.IntegerField()
    parameters = JSONField()
    files = JSONField()
    callback_url = models.CharField(max_length=2048)
    output_location = models.CharField(max_length=2048, blank=True, default='', editable=False)
    date = models.DateTimeField(auto_now_add=True)



    @property
    def __str__(self):
        return self.name


# Add a token upon user creation
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(author=instance)
        # user?
