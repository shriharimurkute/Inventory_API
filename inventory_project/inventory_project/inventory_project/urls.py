"""
URL configuration for inventory_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# inventory_project/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views as authtoken_views
from django.views.generic.base import RedirectView
from inventory_api import views as api_views # Import your app's views

urlpatterns = [
    # Redirect root to the new UI page
    path('', RedirectView.as_view(url='/inventory/', permanent=False), name='index'),

    # URL for the frontend interface
    path('inventory/', api_views.inventory_ui, name='inventory_ui'), # <-- New UI URL

    path('admin/', admin.site.urls),
    path('api/v1/', include('inventory_api.urls')), # Your app's API URLs
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', authtoken_views.obtain_auth_token, name='api_token_auth'),
]