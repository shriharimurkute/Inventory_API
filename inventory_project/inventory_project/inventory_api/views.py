from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import InventoryItem
from .serializers import InventoryItemSerializer
from .permissions import IsOwnerOrReadOnly # Optional: Custom permission

# Using ModelViewSet provides default CRUD actions (list, create, retrieve, update, partial_update, destroy)
class InventoryItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows inventory items to be viewed or edited.
    """
    queryset = InventoryItem.objects.all().order_by('-date_added') # Get all items, newest first
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users can access

    # Optional: Custom permission - only the user who added the item can modify/delete it
    # permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        """
        Associate the item with the user making the request upon creation.
        """
        serializer.save(added_by=self.request.user)

    # Example: Custom action (e.g., increase quantity)
    # from rest_framework.decorators import action
    # @action(detail=True, methods=['post'])
    # def increase_quantity(self, request, pk=null):
    #     item = self.get_object()
    #     amount = request.data.get('amount', 1) # Get amount from request body, default 1
    #     try:
    #         amount = int(amount)
    #         if amount <= 0:
    #             raise ValueError("Amount must be positive.")
    #         item.quantity += amount
    #         item.save()
    #         serializer = self.get_serializer(item)
    #         return Response(serializer.data)
    #     except (TypeError, ValueError) as e:
    #         return Response({'error': f'Invalid amount: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    # Override querysets if needed (e.g., only show items added by the user)
    # def get_queryset(self):
    #    """
    #    Optionally restricts the returned purchases to a given user,
    #    by filtering against a `username` query parameter in the URL.
    #    """
    #    user = self.request.user
    #    if user.is_staff: # Admins see everything
    #        return InventoryItem.objects.all()
    #    return InventoryItem.objects.filter(added_by=user)
    

    # inventory_api/views.py
# ... other imports
from django.http import HttpResponse

def home(request):
    # You can make this more complex, render a template, etc.
    html_content = """
    <h1>Welcome to the Inventory API</h1>
    <p>This is the backend API service.</p>
    <p>Access the main API endpoint:</p>
    <ul>
        <li><a href="/api/v1/">/api/v1/</a> (Browsable API)</li>
        <li><a href="/api-token-auth/">/api-token-auth/</a> (Get Auth Token)</li>
    </ul>
    <p>Access the admin interface:</p>
    <ul>
        <li><a href="/admin/">/admin/</a></li>
    </ul>
    """
    return HttpResponse(html_content)


# New view for the frontend UI
def inventory_ui(request):
    """Renders the main inventory management interface template."""
    return render(request, 'inventory_api/inventory.html')