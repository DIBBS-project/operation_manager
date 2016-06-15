# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Execution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('process_id', models.IntegerField()),
                ('parameters', jsonfield.fields.JSONField(default=dict)),
                ('files', jsonfield.fields.JSONField(default=dict)),
                ('callback_url', models.CharField(max_length=2048)),
                ('mrcluster_token', models.CharField(max_length=128)),
                ('output_location', models.CharField(default=b'', max_length=2048, editable=False, blank=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(max_length=2048, blank=True)),
                ('status_info', models.CharField(max_length=2048, blank=True)),
                ('author', models.ForeignKey(related_name='executions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
