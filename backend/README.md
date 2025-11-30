# Image Upload API

FastAPI application for uploading user images (front, side, and back views).

## Setup

1. Install `uv` (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or using pip
   pip install uv
   ```
   For other installation methods, see: https://github.com/astral-sh/uv

2. Set up environment variables:
   
   Create a `.env` file in the project root directory:
   
   ```bash
   # Required for image generation with Gemini
   IMAGE_API_KEY=your_image_api_key_here
   
   # Optional: for product search via Google Custom Search
   GOOGLE_API_KEY=your_google_api_key_here
   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
   ```
   
   To get these credentials:
   - **IMAGE_API_KEY**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
     - Make sure to enable the "Gemini API" in your Google Cloud Console
     - The API key must have permission to use `generativelanguage.googleapis.com`
   - **GOOGLE_API_KEY** and **GOOGLE_SEARCH_ENGINE_ID**: For product search (optional)
     - Get from [Google Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/all)
   
   Note: 
   - Product search will be skipped if `GOOGLE_SEARCH_ENGINE_ID` is not configured
   - Image generation will be skipped if `GOOGLE_API_KEY` is not configured
   - Other features will still work without these

3. Install dependencies using `uv`:
   
   **Option 1: Using uv sync (recommended - uses pyproject.toml):**
   ```bash
   # From project root
   uv sync
   ```
   This will create a virtual environment at `.venv` and install all dependencies.
   
   **Option 2: Using uv pip (alternative - uses requirements.txt):**
   ```bash
   # From project root
   uv pip install -r backend/requirements.txt
   ```
   
   **Option 3: Using pip (alternative):**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Run the server:

**Option 1: Using uv run (recommended):**
```bash
# From project root
uv run uvicorn backend.main:app --reload
```

**Option 2: Using Python directly:**
```bash
cd backend
python main.py
```

**Option 3: Using uvicorn directly (make sure you're in the backend directory):**
```bash
cd backend
uvicorn main:app --reload
```

**Option 4: From the project root directory:**
```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /save-preferences

Save user preferences and automatically search for relevant products.

**Request Body (JSON):**
```json
{
  "user_folder": "data/user_images/user123",
  "gender": "male",
  "size": "M",
  "styles": ["casual", "sporty"],
  "clothing_types": ["tops", "bottoms"],
  "budget": "medium",
  "colors": "black, navy",
  "notes": "Looking for comfortable everyday wear"
}
```

**Response:**
```json
{
  "message": "Preferences saved successfully",
  "preferences_file": "data/user_images/user123/preferences.json",
  "preferences": { ... },
  "recommended_products": [
    {
      "title": "Product Title",
      "link": "https://...",
      "snippet": "Product description..."
    }
  ],
  "products_count": 5
}
```

### POST /upload-images

Upload three images (front, side, back) for a user.

**Parameters:**
- `front` (file): Front view image
- `side` (file): Side view image  
- `back` (file): Back view image
- `user_id` (optional, form field): User identifier (if not provided, uses timestamp)

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/upload-images" \
  -F "front=@/path/to/front.jpg" \
  -F "side=@/path/to/side.jpg" \
  -F "back=@/path/to/back.jpg" \
  -F "user_id=user123"
```

**Example using Python requests:**
```python
import requests

url = "http://localhost:8000/upload-images"
files = {
    'front': open('front.jpg', 'rb'),
    'side': open('side.jpg', 'rb'),
    'back': open('back.jpg', 'rb')
}
data = {'user_id': 'user123'}  # Optional

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response:**
```json
{
  "message": "Images uploaded successfully",
  "user_folder": "data/user_images/user123",
  "saved_files": {
    "front": "data/user_images/user123/front.jpg",
    "side": "data/user_images/user123/side.jpg",
    "back": "data/user_images/user123/back.jpg"
  }
}
```

## Virtual Try-On Image Generation

The system uses Google's Gemini 2.0 Flash model to generate images of users wearing the found clothing items.

After saving preferences, the system will:
1. Search for relevant products
2. Download product images
3. Generate combined images showing the user wearing each product from all 3 angles (front, side, back)

Generated images are saved to: `data/user_images/{user_id}/combined_images/`

**Requirements:**
1. Set `IMAGE_API_KEY` in your `.env` file
2. Enable the Gemini API in Google Cloud Console:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable "Generative Language API" for your project
   - Make sure billing is enabled (free tier available)
3. Generate an API key at [Google AI Studio](https://aistudio.google.com/app/apikey)

**Common Issues:**
- If you see `API_KEY_SERVICE_BLOCKED` error, the Gemini API is not enabled for your API key
- If image generation fails, the system will continue with other features
- Product search can use web scraping if Google Search is not configured

**Note:** The image generation feature requires a valid Gemini API key (`IMAGE_API_KEY`). If not configured, the app will still work for:
- Image uploads
- Preference saving
- Product search (via web scraping)

## File Structure

Images and preferences are stored in `data/user_images/` with the following structure:
```
data/
  user_images/
    user_id_1/
      front.jpg
      side.jpg
      back.jpg
      preferences.json
      products/
        product_images/
          product_1_*.jpg
          product_2_*.jpg
          ...
        product_links/
          product_1_link.txt
          product_2_link.txt
          ...
      combined_images/
        product_1_front_*.png
        product_1_side_*.png
        product_1_back_*.png
        product_2_front_*.png
        ...
    user_id_2/
      front.jpg
      side.jpg
      back.jpg
      preferences.json
      products/
        ...
      combined_images/
        ...
```

## Features

- ✅ Image upload (front, side, back views)
- ✅ User preferences collection (gender, size, styles, clothing types, budget, colors, notes)
- ✅ Automatic product search based on preferences (requires Google Custom Search API credentials)
- ✅ Product image download and storage
- ⏳ Virtual Try-On image generation (placeholder - requires additional setup)
  - Framework in place for generating combined images
  - Would show user wearing products from all 3 angles
  - Requires Google Cloud Vertex AI Virtual Try-On API access

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

