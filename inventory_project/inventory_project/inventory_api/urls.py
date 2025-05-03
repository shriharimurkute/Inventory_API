from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryItemViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'items', InventoryItemViewSet, basename='inventoryitem') # 'items' is the URL prefix

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]