// API endpoint - adjust this if your backend is running on a different port/URL
const API_URL = 'http://localhost:8000';

// Get form elements
const form = document.getElementById('uploadForm');
const frontInput = document.getElementById('front');
const sideInput = document.getElementById('side');
const backInput = document.getElementById('back');
const submitBtn = document.getElementById('submitBtn');
const submitText = document.getElementById('submitText');
const submitLoader = document.getElementById('submitLoader');
const messageDiv = document.getElementById('message');

// File input elements
const fileInputs = {
    front: frontInput,
    side: sideInput,
    back: backInput
};

// Preview elements
const previews = {
    front: document.getElementById('frontPreview'),
    side: document.getElementById('sidePreview'),
    back: document.getElementById('backPreview')
};

// File name elements
const fileNames = {
    front: document.getElementById('frontFileName'),
    side: document.getElementById('sideFileName'),
    back: document.getElementById('backFileName')
};

// Initialize preview handlers for each file input
Object.keys(fileInputs).forEach(key => {
    const input = fileInputs[key];
    const preview = previews[key];
    const fileName = fileNames[key];
    const uploadBox = input.closest('.upload-label').querySelector('.upload-box');

    // Handle file selection
    input.addEventListener('change', (e) => {
        handleFileSelect(e, key, preview, fileName);
    });

    // Handle drag and drop
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('drag-over');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('drag-over');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            handleFileSelect({ target: input }, key, preview, fileName);
        }
    });
});

// Handle file selection and preview
function handleFileSelect(event, key, preview, fileName) {
    const file = event.target.files[0];
    if (file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            showMessage('Please select an image file', 'error');
            event.target.value = '';
            return;
        }

        // Show file name
        fileName.textContent = file.name;

        // Create and show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.innerHTML = `<img src="${e.target.result}" alt="${key} preview">`;
            preview.classList.add('show');
        };
        reader.readAsDataURL(file);
    }
}

// Handle form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Validate that all files are selected
    if (!frontInput.files[0] || !sideInput.files[0] || !backInput.files[0]) {
        showMessage('Please select all three images (front, side, and back)', 'error');
        return;
    }

    // Disable submit button and show loading state
    submitBtn.disabled = true;
    submitText.style.display = 'none';
    submitLoader.style.display = 'block';
    hideMessage();

    try {
        // Create FormData
        const formData = new FormData();
        formData.append('front', frontInput.files[0]);
        formData.append('side', sideInput.files[0]);
        formData.append('back', backInput.files[0]);

        const userId = document.getElementById('user_id').value.trim();
        if (userId) {
            formData.append('user_id', userId);
        }

        // Send request to API
        const response = await fetch(`${API_URL}/upload-images`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(
                `Images uploaded successfully! Redirecting to preferences...`,
                'success'
            );
            // Redirect to preferences page after 1.5 seconds
            setTimeout(() => {
                window.location.href = `preferences.html?userFolder=${encodeURIComponent(data.user_folder)}`;
            }, 1500);
        } else {
            showMessage(data.error || 'Failed to upload images', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage(
            `Error: ${error.message}. Make sure the backend server is running on ${API_URL}`,
            'error'
        );
    } finally {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitText.style.display = 'block';
        submitLoader.style.display = 'none';
    }
});

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

