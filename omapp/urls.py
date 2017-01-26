# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'instances', views.InstanceViewSet)
router.register(r'executions', views.ExecutionViewSet)
# router.register(r'users', views.UserViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    url(r'^', include(router.urls)),
]
