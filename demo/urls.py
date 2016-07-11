from django.conf.urls import url, include
from demo import views


urlpatterns = [
    url(r'^index/',  views.index, name='index'),
    url(r'^executions/',  views.executions, name='executions'),
    url(r'^process_instances/',  views.process_instances, name='process_instances'),
    url(r'^$',  views.index, name='index'),
    url(r'^details/(?P<pk>[0-9]+)/$', views.show_details,  name='execution_details'),
    url(r'^execution_form/',  views.create_execution, name='execution_form'),
    url(r'^process_instance_form/',  views.create_process_instance, name='process_instance_form'),
]
