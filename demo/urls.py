from django.conf.urls import url, include
from demo import views


urlpatterns = [
    url(r'^index/',  views.index, name='index'),
    url(r'^executions/',  views.executions, name='executions'),
    url(r'^$',  views.index, name='index'),
    url(r'^details/(?P<pk>[0-9]+)/$', views.show_details,  name='execution_details'),
]
