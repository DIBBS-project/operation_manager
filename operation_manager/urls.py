# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from django.conf.urls import include, url
from django.contrib import admin

# import demo.views as demo_views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    # url(r'^demo/', include('demo.urls')),
    url(r'^', include('omapp.urls')),
]
