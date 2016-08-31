from django.conf.urls import url, include
from omapp import views
from rest_framework.routers import DefaultRouter
import rest_framework.authtoken.views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'instances', views.InstanceViewSet)
router.register(r'executions', views.ExecutionViewSet)
router.register(r'users', views.UserViewSet)

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^exec/(?P<pk>[0-9]+)/run/$', views.run_execution),
]


# Allows to get a token by sending credentials
urlpatterns += [
    url(r'^api-token-auth/', rest_framework.authtoken.views.obtain_auth_token)
]
