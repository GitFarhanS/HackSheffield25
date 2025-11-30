# Frontend - Image Upload Interface

A modern, responsive web interface for uploading front, side, and back view images.

## Features

- ✨ Modern, clean UI with gradient design
- 📸 Image preview before upload
- 🖱️ Drag and drop support
- 📱 Fully responsive (mobile-friendly)
- ⚡ Real-time upload status
- ✅ Form validation
- 🎯 User ID support (optional)

## Setup

### Option 1: Using a Simple HTTP Server (Recommended)

Since this is a static frontend, you can serve it using Python's built-in HTTP server:

```bash
cd frontend
python3 -m http.server 8080
```

Then open your browser and navigate to: `http://localhost:8080`

### Option 2: Using Node.js http-server

If you have Node.js installed:

```bash
cd frontend
npx http-server -p 8080
```

### Option 3: Using VS Code Live Server

If you're using VS Code, you can use the Live Server extension to serve the files.

## Configuration

The frontend is configured to connect to the FastAPI backend at `http://localhost:8000` by default.

If your backend is running on a different URL or port, edit `script.js` and update the `API_URL` constant:

```javascript
const API_URL = 'http://your-backend-url:port';
```

## Usage

1. Make sure the FastAPI backend is running (see backend README)
2. Start the frontend server (see Setup above)
3. Open the frontend in your browser
4. Optionally enter a User ID
5. Select or drag and drop images for:
   - Front view
   - Side view
   - Back view
6. Click "Upload Images"
7. Wait for the success message

## File Structure

```
frontend/
  ├── index.html    # Main HTML structure
  ├── styles.css    # Styling and layout
  ├── script.js     # JavaScript functionality
  └── README.md     # This file
```

## Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Troubleshooting

### CORS Errors

If you encounter CORS (Cross-Origin Resource Sharing) errors, you need to enable CORS in your FastAPI backend. Add this to your `backend/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Backend Not Found

Make sure:
1. The FastAPI backend is running on port 8000
2. The `API_URL` in `script.js` matches your backend URL
3. There are no firewall issues blocking the connection

