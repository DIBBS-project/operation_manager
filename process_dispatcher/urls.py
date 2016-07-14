from django.conf.urls import include, url
from django.contrib import admin
import demo.views as demo_views

urlpatterns = [
    # Examples:
    # url(r'^$', 'process_registry.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^demo/', include('demo.urls')),
    url(r'^', include('pdapp.urls')),
]
