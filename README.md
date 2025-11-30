# StyleSwipe 👗✨

A modern AI-powered virtual try-on application that helps users discover and visualize clothing items that match their personal style preferences. Built with FastAPI, PostgreSQL, and Google's Gemini AI.

## 🎯 What is StyleSwipe?

StyleSwipe is a Tinder-style swiping interface for clothing discovery. Users upload photos of themselves, specify their style preferences, and then swipe through AI-generated images showing them wearing different clothing items. The app uses Google Shopping API to find real products and Google's Gemini AI to generate realistic virtual try-on images.

## ✨ Key Features

### 📸 Image Upload & Processing
- Upload three photos (front, side, back views) of yourself
- Supports both JPG and PNG formats
- Automatic image compression and optimization
- Images stored securely in user-specific folders

### 🎨 Style Preferences
- Comprehensive preference form:
  - Gender and size selection
  - Multiple clothing styles (casual, formal, sporty, streetwear, vintage, etc.)
  - Clothing types (tops, bottoms, outerwear, shoes, accessories, etc.)
  - Budget range and color preferences
  - Additional notes for specific requirements

### 🔍 Smart Product Search
- Integrates with Google Shopping API via SerpApi
- Searches UK retailers for products matching user preferences
- Downloads product images and links
- Saves product metadata (price, rating, reviews, source)

### ✨ AI-Powered Virtual Try-On
- Uses Google Gemini AI to generate realistic try-on images
- Creates combined images from three angles (front, side, back)
- All generated images in 9:16 aspect ratio (perfect for mobile viewing)
- High-quality image generation with natural clothing fit

### 👆 Tinder-Style Swiping
- Intuitive swipe interface:
  - **Tap card** → Cycle through front/side/back views
  - **Swipe right** → Like the item
  - **Swipe left** → Dislike the item
- Smooth animations and drag interactions
- Progress tracking (X / Y products swiped)

### 💾 Results & Analytics
- View all liked items in a beautiful results page
- See product details: title, price, source, ratings
- Direct links to purchase products
- All data stored in PostgreSQL for analytics

### 📊 Grafana Integration
- Full PostgreSQL database for analytics
- Track product clicks, swipe patterns, and user preferences
- Create dashboards for:
  - Click-through rates
  - Popular product types
  - User engagement metrics
  - Conversion funnels

## 🏗️ Architecture

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database for all data
- **SQLAlchemy** - ORM for database operations
- **Google Gemini AI** - Image generation and virtual try-on
- **SerpApi** - Google Shopping product search
- **Pillow** - Image processing

### Frontend
- **HTML/CSS/JavaScript** - Modern, responsive design
- **Dark theme** - Beautiful pink/gold gradient accents
- **Touch-friendly** - Swipe gestures for mobile and desktop
- **Loading animations** - Smooth user experience

### Database Schema
- `users` - User accounts and metadata
- `user_images` - Uploaded image paths
- `preferences` - User style preferences
- `products` - Products from search API
- `swipes` - Swipe history (liked/disliked)
- `liked_products` - Saved liked items
- `product_clicks` - Click tracking for analytics

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL (or Docker for containerized setup)
- `uv` package manager (or pip)
- API keys:
  - Google Gemini API key (for image generation)
  - SerpApi key (for product search)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Hacksheffielf
   ```

2. **Set up PostgreSQL**
   ```bash
   # Using Docker (recommended)
   docker-compose up -d
   
   # Or install PostgreSQL locally
   ```

3. **Install dependencies**
   ```bash
   uv sync
   # Or: pip install -r backend/requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   # Database
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/styleswipe
   
   # Google Gemini API (for image generation)
   IMAGE_API_KEY=your_gemini_api_key_here
   
   # SerpApi (for product search)
   SERPI_API=your_serpapi_key_here
   ```

5. **Initialize database**
   ```bash
   uv run python -c "from backend.database import init_db; init_db()"
   ```

6. **Start the backend**
   ```bash
   uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Start the frontend**
   ```bash
   cd frontend
   python3 -m http.server 3000
   ```

8. **Open in browser**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📖 Usage

### For Users

1. **Upload Photos**
   - Go to http://localhost:3000
   - Upload front, side, and back view photos
   - Click "Continue to Preferences"

2. **Set Preferences**
   - Fill in your style preferences
   - Select clothing types and styles you like
   - Click "Find My Looks"

3. **Wait for Processing**
   - Watch the loading screen as products are searched
   - Images are downloaded and processed
   - AI generates virtual try-on images

4. **Swipe Through Products**
   - Tap cards to see different angles
   - Swipe right to like, left to dislike
   - Track your progress

5. **View Results**
   - See all your liked items
   - Click "View & Purchase" to buy products
   - Share your favorites

### For Developers

#### API Endpoints

- `POST /upload-images` - Upload user photos
- `POST /save-preferences` - Save style preferences and trigger search
- `GET /api/swipe/{user_folder}/products` - Get products for swiping
- `POST /api/swipe/{user_folder}/action` - Record swipe action
- `GET /api/swipe/{user_folder}/liked` - Get liked products
- `POST /api/product/click` - Track product clicks

See full API documentation at http://localhost:8000/docs

#### Database Queries

Example queries for Grafana dashboards are in `DATABASE_SETUP.md`.

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI/ML**: Google Gemini AI (image generation)
- **APIs**: SerpApi (Google Shopping)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Image Processing**: Pillow (PIL)
- **Deployment**: Docker, Docker Compose

## 📁 Project Structure

```
Hacksheffielf/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── search_products.py   # Product search (SerpApi)
│   ├── generate_images.py   # AI image generation
│   └── swiping_system.py    # Swipe logic
├── frontend/
│   ├── index.html          # Upload page
│   ├── preferences.html    # Preferences form
│   ├── swipe.html          # Swiping interface
│   ├── theme.css           # Shared theme
│   └── *.js, *.css        # Frontend logic
├── data/
│   └── user_images/        # User uploads
├── docker-compose.yml      # PostgreSQL setup
├── pyproject.toml          # Dependencies
└── README.md              # This file
```

## 🔐 Security & Privacy

- User images stored locally in `data/user_images/`
- Database credentials in `.env` (not committed)
- API keys stored securely in environment variables
- CORS configured for development (update for production)

## 📊 Analytics & Monitoring

- PostgreSQL database for all user interactions
- Grafana integration for dashboards
- Track:
  - User signups and preferences
  - Product searches and results
  - Swipe patterns (likes/dislikes)
  - Click-through rates
  - Popular products and categories

## 🚧 Future Enhancements

- [ ] User authentication and accounts
- [ ] Social sharing of favorite looks
- [ ] Wishlist functionality
- [ ] Price tracking and alerts
- [ ] Multiple style profiles per user
- [ ] Integration with more retailers
- [ ] Mobile app (React Native)
- [ ] Real-time notifications

## 📝 License

This project is part of HackSheffield hackathon.

## 👥 Contributing

This is a hackathon project. Contributions and suggestions are welcome!

## 🙏 Acknowledgments

- Google Gemini AI for image generation
- SerpApi for product search
- FastAPI for the excellent web framework
- PostgreSQL community for the robust database

---

**Built with ❤️ for HackSheffield**

