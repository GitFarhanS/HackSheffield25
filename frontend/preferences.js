// API endpoint
const API_URL = 'http://localhost:8000';

// Get form elements
const form = document.getElementById('preferencesForm');
const submitBtn = document.getElementById('submitBtn');
const submitText = document.getElementById('submitText');
const submitLoader = document.getElementById('submitLoader');
const messageDiv = document.getElementById('message');
const backBtn = document.getElementById('backBtn');
const userFolderInput = document.getElementById('userFolder');

// Get user folder from URL parameters
const urlParams = new URLSearchParams(window.location.search);
const userFolder = urlParams.get('userFolder');

if (userFolder) {
    userFolderInput.value = userFolder;
} else {
    // If no user folder, redirect back to upload page
    window.location.href = 'index.html';
}

// Handle back button
backBtn.addEventListener('click', () => {
    window.location.href = 'index.html';
});

// Handle form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Collect form data
    const formData = {
        user_folder: userFolder,
        gender: document.getElementById('gender').value,
        size: document.getElementById('size').value,
        styles: [],
        clothing_types: [],
        budget: document.getElementById('budget').value,
        colors: document.getElementById('colors').value.trim(),
        notes: document.getElementById('notes').value.trim()
    };

    // Validate required fields
    if (!formData.gender) {
        showMessage('Please select your gender', 'error');
        return;
    }

    if (!formData.size) {
        showMessage('Please select your size', 'error');
        return;
    }

    // Collect selected styles
    const styleCheckboxes = form.querySelectorAll('input[name="style"]:checked');
    styleCheckboxes.forEach(checkbox => {
        formData.styles.push(checkbox.value);
    });

    // Collect selected clothing types
    const typeCheckboxes = form.querySelectorAll('input[name="clothing_types"]:checked');
    typeCheckboxes.forEach(checkbox => {
        formData.clothing_types.push(checkbox.value);
    });

    // Validate that at least one style and one clothing type is selected
    if (formData.styles.length === 0) {
        showMessage('Please select at least one clothing style', 'error');
        return;
    }

    if (formData.clothing_types.length === 0) {
        showMessage('Please select at least one clothing type', 'error');
        return;
    }

    // Disable submit button and show loading state
    submitBtn.disabled = true;
    submitText.style.display = 'none';
    submitLoader.style.display = 'block';
    hideMessage();

    try {
        // Send request to API
        const response = await fetch(`${API_URL}/save-preferences`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Preferences saved! Redirecting to try-on experience...', 'success');
            
            // Store user folder in localStorage for the swipe page
            localStorage.setItem('userFolder', userFolder);
            
            // Redirect to swipe page with loading screen
            setTimeout(() => {
                window.location.href = `swipe.html?user=${encodeURIComponent(userFolder)}&loading=true`;
            }, 1000);
        } else {
            showMessage(data.error || 'Failed to save preferences', 'error');
            // Re-enable submit button on error
            submitBtn.disabled = false;
            submitText.style.display = 'block';
            submitLoader.style.display = 'none';
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage(
            `Error: ${error.message}. Make sure the backend server is running on ${API_URL}`,
            'error'
        );
        // Re-enable submit button on error
        submitBtn.disabled = false;
        submitText.style.display = 'block';
        submitLoader.style.display = 'none';
    }
});

// Also store user folder on page load for easier access
if (userFolder) {
    localStorage.setItem('userFolder', userFolder);
}

// Show message function
function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = `message show ${type}`;
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            hideMessage();
        }, 5000);
    }
}

// Hide message function
function hideMessage() {
    messageDiv.classList.remove('show');
}

