from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User # Link items to the user who added them

class InventoryItem(models.Model):
    """
    Represents an item in the inventory.
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit")
    added_by = models.ForeignKey(User, related_name='inventory_items', on_delete=models.SET_NULL, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name'] # Default ordering

    def __str__(self):
        return f"{self.name} (Qty: {self.quantity})"