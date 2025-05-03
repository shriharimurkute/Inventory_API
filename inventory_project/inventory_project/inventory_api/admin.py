from django.contrib import admin
from .models import InventoryItem

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit_price', 'added_by', 'date_added', 'last_updated')
    list_filter = ('date_added', 'added_by')
    search_fields = ('name', 'description')
    readonly_fields = ('date_added', 'last_updated')
    # Optional: Make added_by readonly in admin if set automatically
    # readonly_fields = ('added_by', 'date_added', 'last_updated')

    # If using IsOwnerOrReadOnly, you might want admins to bypass this in admin
    # def get_queryset(self, request):
    #    qs = super().get_queryset(request)
    #    if request.user.is_superuser:
    #        return qs
    #    return qs.filter(added_by=request.user)

    # def save_model(self, request, obj, form, change):
    #    if not obj.pk: # If creating new object
    #        obj.added_by = request.user
    #    super().save_model(request, obj, form, change)