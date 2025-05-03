from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from ..models import InventoryItem
from ..serializers import InventoryItemSerializer
import decimal # For precise decimals in tests

# --- Helper to create users and items ---
def create_user(username='testuser', password='password123', email='test@example.com', is_staff=False):
    return User.objects.create_user(username=username, password=password, email=email, is_staff=is_staff)

def create_inventory_item(user, name='Test Item', quantity=10, price='19.99'):
    return InventoryItem.objects.create(
        name=name,
        quantity=quantity,
        unit_price=decimal.Decimal(price),
        added_by=user
    )

# --- Test Cases ---
class InventoryItemApiTests(APITestCase):

    def setUp(self):
        # Create users
        self.user1 = create_user('user1', 'pwd1')
        self.user2 = create_user('user2', 'pwd2')
        self.admin_user = create_user('admin', 'pwdadmin', is_staff=True)

        # Create tokens for authentication
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        self.admin_token = Token.objects.create(user=self.admin_user)

        # API Client
        self.client = APIClient()

        # Create some initial items
        self.item1 = create_inventory_item(self.user1, name='Item A', quantity=5, price='10.00')
        self.item2 = create_inventory_item(self.user2, name='Item B', quantity=20, price='5.50')

        # URLs (using reverse for maintainability)
        self.list_create_url = reverse('inventoryitem-list') # Corresponds to '/api/v1/items/'
        self.detail_url = lambda pk: reverse('inventoryitem-detail', kwargs={'pk': pk}) # '/api/v1/items/{pk}/'

    # --- Authentication Tests ---
    def test_list_items_requires_auth(self):
        """ Ensure listing items requires authentication. """
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_item_requires_auth(self):
        """ Ensure creating items requires authentication. """
        data = {'name': 'New Item C', 'quantity': 1, 'unit_price': '1.00'}
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- List and Create Tests (Authenticated) ---
    def test_list_items_authenticated(self):
        """ Test listing items when authenticated. """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if both items are listed (assuming default permissions allow listing all)
        self.assertEqual(len(response.data['results']), 2) # Assuming pagination is on
        self.assertEqual(response.data['results'][0]['name'], self.item2.name) # Default ordering is newest first
        self.assertEqual(response.data['results'][1]['name'], self.item1.name)

    def test_create_item_authenticated(self):
        """ Test creating an item when authenticated. """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        data = {'name': 'New Item C', 'quantity': 15, 'unit_price': '99.99'}
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InventoryItem.objects.count(), 3)
        created_item = InventoryItem.objects.get(name='New Item C')
        self.assertEqual(created_item.added_by, self.user1)
        self.assertEqual(created_item.quantity, 15)
        self.assertEqual(created_item.unit_price, decimal.Decimal('99.99'))
        self.assertEqual(response.data['name'], 'New Item C')
        self.assertEqual(response.data['added_by'], self.user1.username)

    def test_create_item_invalid_data(self):
        """ Test creating an item with invalid data. """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        data = {'name': '', 'quantity': -5, 'unit_price': '-10.00'} # Invalid data
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data) # Check for specific field errors
        self.assertIn('quantity', response.data)
        self.assertIn('unit_price', response.data)
        self.assertEqual(InventoryItem.objects.count(), 2) # Ensure no item was created

    def test_create_item_duplicate_name(self):
        """ Test creating an item with a name that already exists. """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        data = {'name': self.item1.name, 'quantity': 1, 'unit_price': '1.00'} # Duplicate name
        response = self.client.post(self.list_create_url, data, format='json')
        # This depends on whether you added serializer-level validation or rely on model's unique=True
        # If relying on model's unique=True, it might raise IntegrityError -> 500 or DRF handles it -> 400
        # Let's assume DRF or model validation handles it cleanly.
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertEqual(InventoryItem.objects.count(), 2)

    # --- Retrieve, Update, Delete Tests (Authenticated) ---
    def test_retrieve_item_authenticated(self):
        """ Test retrieving a specific item when authenticated. """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.get(self.detail_url(self.item1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = InventoryItemSerializer(self.item1) # Get expected data
        # Compare relevant fields, excluding dynamic ones like last_updated if needed
        self.assertEqual(response.data['id'], serializer.data['id'])
        self.assertEqual(response.data['name'], serializer.data['name'])
        self.assertEqual(int(response.data['quantity']), serializer.data['quantity']) # Compare quantity
        self.assertEqual(decimal.Decimal(response.data['unit_price']), serializer.data['unit_price']) # Compare price

    def test_retrieve_item_not_found(self):
        """ Test retrieving a non-existent item. """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.get(self.detail_url(9999)) # Non-existent PK
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Update Tests (PUT and PATCH) ---
    def test_update_item_put(self):
        """ Test fully updating an item using PUT. """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        data = {'name': 'Updated Item A', 'quantity': 50, 'unit_price': '12.50', 'description': 'New desc'}
        response = self.client.put(self.detail_url(self.item1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item1.refresh_from_db() # Reload data from DB
        self.assertEqual(self.item1.name, 'Updated Item A')
        self.assertEqual(self.item1.quantity, 50)
        self.assertEqual(self.item1.unit_price, decimal.Decimal('12.50'))
        self.assertEqual(self.item1.description, 'New desc')
        self.assertEqual(self.item1.added_by, self.user1) # Ensure owner didn't change

    def test_update_item_patch(self):
        """ Test partially updating an item using PATCH. """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        data = {'quantity': 55} # Only update quantity
        response = self.client.patch(self.detail_url(self.item1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.name, 'Item A') # Name should not change
        self.assertEqual(self.item1.quantity, 55) # Quantity should change
        self.assertEqual(self.item1.unit_price, decimal.Decimal('10.00')) # Price should not change

    # --- Delete Tests ---
    def test_delete_item(self):
        """ Test deleting an item. """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.delete(self.detail_url(self.item1.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(InventoryItem.objects.filter(pk=self.item1.pk).exists())
        self.assertEqual(InventoryItem.objects.count(), 1) # Only item2 should remain

    # --- Permission Tests (If using IsOwnerOrReadOnly) ---
    # Uncomment these if you implement and apply the IsOwnerOrReadOnly permission
    # def test_update_item_permission_denied(self):
    #     """ Test that a user cannot update an item they don't own. """
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}') # User2 trying to update item1
    #     data = {'quantity': 99}
    #     response = self.client.patch(self.detail_url(self.item1.pk), data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.item1.refresh_from_db()
    #     self.assertNotEqual(self.item1.quantity, 99) # Ensure quantity didn't change

    # def test_delete_item_permission_denied(self):
    #     """ Test that a user cannot delete an item they don't own. """
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}') # User2 trying to delete item1
    #     response = self.client.delete(self.detail_url(self.item1.pk))
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.assertTrue(InventoryItem.objects.filter(pk=self.item1.pk).exists()) # Ensure item still exists

    # def test_admin_can_update_any_item(self):
    #     """ Test that an admin user can update any item (depends on permission logic). """
    #     # Note: IsOwnerOrReadOnly does NOT grant admins special access by default.
    #     # You'd need IsAdminUser or a custom permission for this.
    #     # Assuming default IsAuthenticated for this test now.
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
    #     data = {'quantity': 199}
    #     response = self.client.patch(self.detail_url(self.item1.pk), data, format='json')
    #     # If using IsAuthenticated only, this should work.
    #     # If using IsOwnerOrReadOnly, this would fail (403) unless admin check added.
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.item1.refresh_from_db()
    #     self.assertEqual(self.item1.quantity, 199)

    # def test_admin_can_delete_any_item(self):
    #     """ Test that an admin user can delete any item (depends on permission logic). """
    #     # Similar note as above regarding permissions.
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
    #     response = self.client.delete(self.detail_url(self.item1.pk))
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    #     self.assertFalse(InventoryItem.objects.filter(pk=self.item1.pk).exists())


# Add Unit tests for models and serializers in separate files
# (e.g., `test_models.py`, `test_serializers.py`) for better organization.
# Example for test_models.py:
# from django.test import TestCase
# from django.contrib.auth.models import User
# from ..models import InventoryItem
# class InventoryItemModelTest(TestCase):
#     def test_string_representation(self):
#         user = User.objects.create(username='modeltester')
#         item = InventoryItem(name="Test Item", quantity=5, added_by=user)
#         self.assertEqual(str(item), "Test Item (Qty: 5)")

# Example for test_serializers.py:
# from django.test import TestCase
# ...
# class InventoryItemSerializerTest(TestCase):
#     def test_serializer_valid_data(self): ...
#     def test_serializer_invalid_data(self): ...