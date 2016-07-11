from django.contrib import admin

# Register your models here.

from .models import Execution, ProcessInstance

admin.site.register(ProcessInstance)
admin.site.register(Execution)
