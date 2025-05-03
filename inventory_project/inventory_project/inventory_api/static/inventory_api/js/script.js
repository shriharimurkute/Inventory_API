document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const loginSection = document.getElementById('loginSection');
    const inventorySection = document.getElementById('inventorySection');
    const loginForm = document.getElementById('loginForm');
    const logoutButton = document.getElementById('logoutButton');
    const inventoryTableBody = document.getElementById('inventoryTableBody');
    const addItemBtn = document.getElementById('addItemBtn');
    const itemModalElement = document.getElementById('itemModal');
    const itemModal = new bootstrap.Modal(itemModalElement); // Bootstrap Modal instance
    const itemForm = document.getElementById('itemForm');
    const saveItemBtn = document.getElementById('saveItemBtn');
    const itemModalLabel = document.getElementById('itemModalLabel');
    const loginError = document.getElementById('loginError');
    const listError = document.getElementById('listError');
    const modalError = document.getElementById('modalError');

    // --- API Configuration ---
    const API_BASE_URL = '/api/v1'; // Use relative path
    const TOKEN_AUTH_URL = '/api-token-auth/';
    const ITEMS_URL = `${API_BASE_URL}/items/`;

    // --- State ---
    let authToken = localStorage.getItem('authToken');
    let currentEditItemId = null;

    // --- Utility Functions ---
    function displayError(element, message) {
        element.textContent = message;
        element.classList.remove('d-none');
    }

    function clearError(element) {
        element.textContent = '';
        element.classList.add('d-none');
    }

    function getAuthHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Token ${authToken}`
        };
    }

    // --- Authentication ---
    async function loginUser(username, password) {
        clearError(loginError);
        try {
            const response = await fetch(TOKEN_AUTH_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const errorData = await response.json();
                let errorMsg = 'Login failed. Please check your credentials.';
                if (errorData && errorData.non_field_errors) {
                    errorMsg = errorData.non_field_errors.join(' ');
                }
                throw new Error(errorMsg);
            }

            const data = await response.json();
            authToken = data.token;
            localStorage.setItem('authToken', authToken); // Store token
            showInventoryView();

        } catch (error) {
            console.error('Login Error:', error);
            displayError(loginError, error.message);
            authToken = null;
            localStorage.removeItem('authToken');
        }
    }

    function logoutUser() {
        authToken = null;
        localStorage.removeItem('authToken');
        showLoginView();
    }

    // --- UI Updates ---
    function showLoginView() {
        loginSection.classList.remove('d-none');
        inventorySection.classList.add('d-none');
        logoutButton.classList.add('d-none');
        inventorySection.classList.remove('loaded'); // Remove animation class
    }

    function showInventoryView() {
        loginSection.classList.add('d-none');
        inventorySection.classList.remove('d-none');
        logoutButton.classList.remove('d-none');
        clearError(loginError); // Clear any previous login errors
        getItems(); // Fetch items when showing inventory
        // Add class slightly delayed for animation
        setTimeout(() => {
            inventorySection.classList.add('loaded');
         }, 50);
    }

    // --- CRUD Operations ---

    // READ (List)
    async function getItems() {
        if (!authToken) return; // Should not happen if UI is correct, but safeguard
        clearError(listError);
        inventoryTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Loading...</td></tr>'; // Loading indicator

        try {
            const response = await fetch(ITEMS_URL, {
                method: 'GET',
                headers: getAuthHeaders()
            });

            if (response.status === 401) { // Token expired or invalid
                logoutUser(); // Force logout
                displayError(loginError, 'Session expired. Please login again.');
                return;
            }
            if (!response.ok) {
                 throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            displayItems(data.results || []); // Handle pagination if enabled

        } catch (error) {
            console.error('Error fetching items:', error);
            inventoryTableBody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Could not load items.</td></tr>';
            displayError(listError, `Failed to fetch items: ${error.message}`);
        }
    }

    function displayItems(items) {
        inventoryTableBody.innerHTML = ''; // Clear previous items or loading indicator
        if (items.length === 0) {
             inventoryTableBody.innerHTML = '<tr><td colspan="7" class="text-center">No inventory items found.</td></tr>';
             return;
        }

        items.forEach(item => {
            const row = inventoryTableBody.insertRow();
            row.setAttribute('data-id', item.id); // Store ID on the row

            // Format date nicely (optional)
            const lastUpdated = new Date(item.last_updated).toLocaleString();

            row.innerHTML = `
                <td>${item.name}</td>
                <td>${item.description || '-'}</td>
                <td>${item.quantity}</td>
                <td>₹${parseFloat(item.unit_price).toFixed(2)}</td>
                <td>${item.added_by || 'N/A'}</td>
                <td>${lastUpdated}</td>
                <td>
                    <i class="fas fa-edit action-btn btn-edit" title="Edit"></i>
                    <i class="fas fa-trash-alt action-btn btn-delete" title="Delete"></i>
                </td>
            `;
        });
    }

    // CREATE / UPDATE
    async function saveItem() {
        if (!authToken) return;
        clearError(modalError);

        const isEditing = !!currentEditItemId; // Check if we have an ID
        const url = isEditing ? `${ITEMS_URL}${currentEditItemId}/` : ITEMS_URL;
        const method = isEditing ? 'PUT' : 'POST'; // Use PUT for full update, POST for create

        const itemData = {
            name: document.getElementById('itemName').value,
            description: document.getElementById('itemDescription').value,
            quantity: parseInt(document.getElementById('itemQuantity').value, 10),
            unit_price: parseFloat(document.getElementById('itemPrice').value).toFixed(2),
        };

        // Basic frontend validation
        if (!itemData.name || itemData.quantity < 0 || itemData.unit_price < 0) {
             displayError(modalError, "Please fill in Name, and ensure Quantity and Price are non-negative.");
             return;
        }


        try {
            const response = await fetch(url, {
                method: method,
                headers: getAuthHeaders(),
                body: JSON.stringify(itemData)
            });

             if (response.status === 401) {
                logoutUser();
                displayError(loginError, 'Session expired. Please login again.');
                itemModal.hide(); // Hide modal on auth error
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                 // Try to format DRF errors
                 let errorMsg = `Error ${response.status}: Could not save item.`;
                 if (typeof errorData === 'object' && errorData !== null) {
                     errorMsg = Object.entries(errorData)
                         .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
                         .join('; ');
                 }
                throw new Error(errorMsg);
            }

            itemModal.hide(); // Close modal on success
            getItems(); // Refresh the list

        } catch (error) {
            console.error('Error saving item:', error);
             displayError(modalError, error.message);
        }
    }

     // DELETE
    async function deleteItem(itemId) {
        if (!authToken) return;

        // Confirmation dialog
        if (!confirm(`Are you sure you want to delete item ID ${itemId}?`)) {
            return;
        }

        try {
            const response = await fetch(`${ITEMS_URL}${itemId}/`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });

            if (response.status === 401) {
                logoutUser();
                displayError(loginError, 'Session expired. Please login again.');
                return;
            }

            if (!response.ok && response.status !== 204) { // 204 No Content is success for DELETE
                 throw new Error(`HTTP error! status: ${response.status}`);
            }

            getItems(); // Refresh list on success

        } catch (error) {
            console.error('Error deleting item:', error);
            displayError(listError, `Failed to delete item: ${error.message}`); // Show error near list
        }
    }


    // --- Event Listeners ---
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        loginUser(username, password);
    });

    logoutButton.addEventListener('click', logoutUser);

    // Modal: Reset form and state when opening for "Add"
    addItemBtn.addEventListener('click', () => {
        currentEditItemId = null; // Ensure we are adding, not editing
        itemForm.reset(); // Clear form fields
        itemModalLabel.textContent = 'Add New Item';
        clearError(modalError); // Clear previous errors
    });

    // Modal: Handle saving (Create or Update)
    saveItemBtn.addEventListener('click', saveItem);


    // Event Delegation for Edit/Delete buttons in the table
    inventoryTableBody.addEventListener('click', async (e) => {
        const target = e.target;
        const row = target.closest('tr'); // Find the parent row
        if (!row) return; // Click wasn't inside a row

        const itemId = row.getAttribute('data-id');
        if (!itemId) return; // Row doesn't have an ID

        // Handle Edit button click
        if (target.classList.contains('btn-edit')) {
             clearError(modalError);
             itemModalLabel.textContent = `Edit Item (ID: ${itemId})`;
             currentEditItemId = itemId; // Set the ID for editing

             // Fetch item details to pre-fill the form (more robust than reading from table)
             try {
                 const response = await fetch(`${ITEMS_URL}${itemId}/`, { headers: getAuthHeaders() });
                 if (!response.ok) throw new Error('Could not fetch item details');
                 const item = await response.json();

                 document.getElementById('itemName').value = item.name;
                 document.getElementById('itemDescription').value = item.description || '';
                 document.getElementById('itemQuantity').value = item.quantity;
                 document.getElementById('itemPrice').value = parseFloat(item.unit_price).toFixed(2);

                 itemModal.show(); // Show the modal after filling
             } catch (error) {
                  console.error("Error fetching item details for edit:", error);
                  displayError(listError, `Could not load details for item ${itemId}.`);
             }
        }

        // Handle Delete button click
        if (target.classList.contains('btn-delete')) {
            deleteItem(itemId);
        }
    });

    // --- Initial Check ---
    if (authToken) {
        showInventoryView(); // If already logged in (token exists), show inventory
    } else {
        showLoginView(); // Otherwise, show login
    }
});