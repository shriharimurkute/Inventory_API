from rest_framework import serializers
from django.contrib.auth.models import User
from .models import InventoryItem

class InventoryItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the InventoryItem model.
    """
    # Make added_by read-only, it will be set automatically based on the request user
    added_by = serializers.ReadOnlyField(source='added_by.username')
    # You could also use SlugRelatedField or PrimaryKeyRelatedField if you wanted to show IDs

    class Meta:
        model = InventoryItem
        fields = [
            'id',           # Include the ID (primary key)
            'name',
            'description',
            'quantity',
            'unit_price',
            'added_by',
            'date_added',
            'last_updated',
        ]
        read_only_fields = ('date_added', 'last_updated') # These are set automatically

    def validate_quantity(self, value):
        """
        Ensure quantity is not negative (although PositiveIntegerField helps).
        """
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value

    def validate_unit_price(self, value):
        """
        Ensure unit price is not negative.
        """
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative.")
        return value

    # Example of unique validation (handled by model's unique=True, but good for demonstration)
    # def validate_name(self, value):
    #     """ Check if an item with this name already exists (case-insensitive). """
    #     if self.instance: # If updating an existing instance
    #         if InventoryItem.objects.filter(name__iexact=value).exclude(pk=self.instance.pk).exists():
    #             raise serializers.ValidationError("An item with this name already exists.")
    #     else: # If creating a new instance
    #         if InventoryItem.objects.filter(name__iexact=value).exists():
    #             raise serializers.ValidationError("An item with this name already exists.")
    #     return value

# Optional: User Serializer (if you need user-related endpoints)
class UserSerializer(serializers.ModelSerializer):
    inventory_items = serializers.PrimaryKeyRelatedField(many=True, read_only=True) # Or use InventoryItemSerializer

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'inventory_items']