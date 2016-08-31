from django.contrib import admin

# Register your models here.

from .models import Execution, Instance

admin.site.register(Instance)
admin.site.register(Execution)
