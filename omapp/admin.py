# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from django.contrib import admin

from .models import Execution, Instance


admin.site.register(Instance)
admin.site.register(Execution)
