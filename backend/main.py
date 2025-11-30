from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import os
import io
from pathlib import Path
import json
import uvicorn
import time
from PIL import Image

# Handle imports whether running from backend/ or project root
try:
    from search_products import scrape_house_of_fraser
    from generate_images import generate_combined_images_for_all_products
    from swiping_system import SwipingSystem
    from database import get_db, init_db
    from models import User, UserImage, Preference, Product, ProductClick
    from metrics import get_metrics
except ModuleNotFoundError:
    from backend.search_products import scrape_house_of_fraser
    from backend.generate_images import generate_combined_images_for_all_products
    from backend.swiping_system import SwipingSystem
    from backend.database import get_db, init_db
    from backend.models import User, UserImage, Preference, Product, ProductClick
    from backend.metrics import get_metrics

app = FastAPI(title="StyleSwipe API", version="2.0.0")

# Enable CORS to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the base directory for storing images
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "data" / "user_images"

# Create the directory if it doesn't exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Image compression settings
MAX_IMAGE_SIZE = 1024  # Max dimension in pixels for user images
IMAGE_QUALITY = 90  # JPEG quality (higher for user images since they're important)


def compress_image(image_data: bytes, save_path: Path, max_size: int = MAX_IMAGE_SIZE, quality: int = IMAGE_QUALITY) -> dict:
    """
    Compress an uploaded image using Pillow.
    
    Args:
        image_data: Raw image bytes
        save_path: Path where to save the compressed image
        max_size: Maximum dimension (width or height) in pixels
        quality: JPEG quality 1-100
    
    Returns:
        Dict with compression stats
    """
    original_size = len(image_data)
    
    # Open image with Pillow
    img = Image.open(io.BytesIO(image_data))
    original_dimensions = img.size
    
    # Convert to RGB if necessary (handles RGBA, P mode, etc.)
    if img.mode in ('RGBA', 'P', 'LA'):
        # Create white background for transparent images
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize if larger than max_size (maintain aspect ratio)
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    # Save as compressed JPEG
    # Always save as .jpg for consistency
    save_path = save_path.with_suffix('.jpg')
    img.save(save_path, 'JPEG', quality=quality, optimize=True)
    
    compressed_size = save_path.stat().st_size
    reduction = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
    
    return {
        "path": save_path,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "reduction_percent": reduction,
        "original_dimensions": original_dimensions,
        "new_dimensions": img.size
    }


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("Database initialized")


def build_search_query(preferences_data: Dict) -> str:
    """
    Build a search query string from user preferences.
    """
    parts = []
    
    # Core attributes
    if preferences_data.get("gender"):
        parts.append(preferences_data["gender"])
    
    if preferences_data.get("styles"):
        parts.extend(preferences_data["styles"])
    
    if preferences_data.get("clothing_types"):
        parts.extend(preferences_data["clothing_types"])
    
    # Optional
    if preferences_data.get("colors"):
        colors = preferences_data["colors"].strip()
        if colors:
            parts.append(colors)
    
    if preferences_data.get("size"):
        parts.append(f"size {preferences_data['size']}")
    
    # Join everything into a single query string
    return " ".join(part for part in parts if part)


@app.get("/")
async def root():
    return {"message": "StyleSwipe API - Use POST /upload-images to upload front, side, and back images"}


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Exposes application metrics for Grafana/Alloy scraping.
    """
    metrics_output, content_type = get_metrics()
    return Response(content=metrics_output, media_type=content_type)


@app.post("/upload-images")
async def upload_images(
    front: UploadFile = File(..., description="Front view image"),
    side: UploadFile = File(..., description="Side view image"),
    back: UploadFile = File(..., description="Back view image"),
    user_id: Optional[str] = Form(None, description="Optional user identifier"),
    db: Session = Depends(get_db)
):
    """
    Upload three images (front, side, back) for a user.
    Creates user in database and saves image paths.
    """
    try:
        # Generate user folder name
        if user_id:
            user_folder_name = user_id
        else:
            user_folder_name = f"user_{int(time.time())}"
        
        user_folder = IMAGES_DIR / user_folder_name
        
        # Create user-specific folder
        user_folder.mkdir(parents=True, exist_ok=True)
        
        # Get or create user in database
        user = db.query(User).filter(User.user_folder == user_folder_name).first()
        if not user:
            user = User(user_folder=user_folder_name)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Define image types and their corresponding files
        image_types = {
            "front": front,
            "side": side,
            "back": back
        }
        
        saved_files = {}
        compression_stats = {}
        
        # Save and compress each image
        for image_type, file in image_types.items():
            # Create file path (will be saved as .jpg after compression)
            file_path = user_folder / f"{image_type}.jpg"
            
            # Read the file
            contents = await file.read()
            
            # Compress and save the image
            stats = compress_image(contents, file_path)
            file_path = stats["path"]  # Get the actual saved path (.jpg)
            
            saved_files[image_type] = str(file_path.relative_to(BASE_DIR))
            compression_stats[image_type] = {
                "original_kb": round(stats["original_size"] / 1024, 1),
                "compressed_kb": round(stats["compressed_size"] / 1024, 1),
                "reduction": f"{stats['reduction_percent']:.0f}%",
                "dimensions": f"{stats['new_dimensions'][0]}x{stats['new_dimensions'][1]}"
            }
            
            print(f"   📦 {image_type}: {stats['original_size']/1024:.1f}KB → {stats['compressed_size']/1024:.1f}KB ({stats['reduction_percent']:.0f}% reduction)")
            
            # Save to database
            user_image = UserImage(
                user_id=user.id,
                angle=image_type,
                image_path=str(file_path.relative_to(BASE_DIR))
            )
            db.add(user_image)
        
        db.commit()
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Images uploaded and compressed successfully",
                "user_folder": str(user_folder.relative_to(BASE_DIR)),
                "user_id": user.id,
                "saved_files": saved_files,
                "compression": compression_stats
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to upload images: {str(e)}"}
        )


# Pydantic model for preferences
class PreferencesRequest(BaseModel):
    user_folder: str
    gender: str
    size: str
    styles: List[str]
    clothing_types: List[str]
    budget: Optional[str] = None
    colors: Optional[str] = None
    notes: Optional[str] = None


@app.post("/save-preferences")
async def save_preferences(
    preferences: PreferencesRequest,
    db: Session = Depends(get_db)
):
    """
    Save user clothing preferences to database.
    """
    try:
        # Get user from database
        user_folder_name = preferences.user_folder.split("/")[-1]
        user = db.query(User).filter(User.user_folder == user_folder_name).first()
        
        if not user:
            return JSONResponse(
                status_code=404,
                content={"error": "User not found. Please upload images first."}
            )
        
        # Get or create preferences
        pref = db.query(Preference).filter(Preference.user_id == user.id).first()
        if pref:
            # Update existing
            pref.gender = preferences.gender
            pref.size = preferences.size
            pref.styles = preferences.styles
            pref.clothing_types = preferences.clothing_types
            pref.budget = preferences.budget
            pref.colors = preferences.colors
            pref.notes = preferences.notes
        else:
            # Create new
            pref = Preference(
                user_id=user.id,
                gender=preferences.gender,
                size=preferences.size,
                styles=preferences.styles,
                clothing_types=preferences.clothing_types,
                budget=preferences.budget,
                colors=preferences.colors,
                notes=preferences.notes
            )
            db.add(pref)
        
        db.commit()
        db.refresh(pref)
        
        # Build preferences dict for search
        preferences_data = {
            "gender": preferences.gender,
            "size": preferences.size,
            "styles": preferences.styles,
            "clothing_types": preferences.clothing_types,
            "budget": preferences.budget,
            "colors": preferences.colors,
            "notes": preferences.notes
        }
        
        # Search for products and save to database
        user_folder_path = BASE_DIR / preferences.user_folder
        search_results = []
        
        try:
            query = build_search_query(preferences_data)
            if query:
                # This will save products to database via search_products.py
                search_results = scrape_house_of_fraser(
                    query, 
                    str(user_folder_path), 
                    db=db,
                    preferences_data=preferences_data
                )
            
            # Generate combined images
            if search_results:
                try:
                    print(f"Generating combined images for {len(search_results)} products...")
                    generated_images = generate_combined_images_for_all_products(str(user_folder_path))
                    print(f"Generated {sum(len(v) for v in generated_images.values())} combined images")
                except Exception as gen_error:
                    print(f"Image generation error (non-fatal): {gen_error}")
        except Exception as search_error:
            print(f"Search error (non-fatal): {search_error}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Preferences saved successfully",
                "preferences": {
                    "gender": pref.gender,
                    "size": pref.size,
                    "styles": pref.styles,
                    "clothing_types": pref.clothing_types,
                    "budget": pref.budget,
                    "colors": pref.colors,
                    "notes": pref.notes
                },
                "recommended_products": search_results,
                "products_count": len(search_results)
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to save preferences: {str(e)}"}
        )


# ==================== SWIPING SYSTEM ENDPOINTS ====================

class SwipeRequest(BaseModel):
    product_id: int
    liked: bool


@app.get("/api/swipe/{user_folder:path}/products")
async def get_swipe_products(user_folder: str, db: Session = Depends(get_db)):
    """Get all products available for swiping."""
    try:
        user_folder_name = user_folder.split("/")[-1]
        swiper = SwipingSystem(user_folder_name, db)
        products = swiper.get_products()
        return JSONResponse(
            status_code=200,
            content={
                "products": products,
                "total": len(products)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/swipe/{user_folder:path}/next")
async def get_next_product(user_folder: str, db: Session = Depends(get_db)):
    """Get the next product to swipe on."""
    try:
        user_folder_name = user_folder.split("/")[-1]
        swiper = SwipingSystem(user_folder_name, db)
        product = swiper.get_next_product()
        status = swiper.get_swipe_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "product": product,
                "status": status
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/swipe/{user_folder:path}/action")
async def swipe_action(
    user_folder: str,
    swipe: SwipeRequest,
    db: Session = Depends(get_db)
):
    """Record a swipe action (like/dislike)."""
    try:
        user_folder_name = user_folder.split("/")[-1]
        swiper = SwipingSystem(user_folder_name, db)
        result = swiper.swipe(swipe.product_id, swipe.liked)
        return JSONResponse(
            status_code=200,
            content=result
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/swipe/{user_folder:path}/status")
async def get_swipe_status(user_folder: str, db: Session = Depends(get_db)):
    """Get current swiping status."""
    try:
        user_folder_name = user_folder.split("/")[-1]
        swiper = SwipingSystem(user_folder_name, db)
        status = swiper.get_swipe_status()
        return JSONResponse(
            status_code=200,
            content=status
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/swipe/{user_folder:path}/liked")
async def get_liked_products(user_folder: str, db: Session = Depends(get_db)):
    """Get all liked products."""
    try:
        user_folder_name = user_folder.split("/")[-1]
        swiper = SwipingSystem(user_folder_name, db)
        liked = swiper.get_liked_products()
        return JSONResponse(
            status_code=200,
            content={
                "liked_products": liked,
                "total": len(liked)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/swipe/{user_folder:path}/reset")
async def reset_swipes(user_folder: str, db: Session = Depends(get_db)):
    """Reset all swipe data."""
    try:
        user_folder_name = user_folder.split("/")[-1]
        swiper = SwipingSystem(user_folder_name, db)
        result = swiper.reset_swipes()
        return JSONResponse(
            status_code=200,
            content=result
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# ==================== PRODUCT CLICK TRACKING ====================

class ProductClickRequest(BaseModel):
    product_id: int
    referrer: Optional[str] = None


@app.post("/api/product/click")
async def track_product_click(
    click: ProductClickRequest,
    user_folder: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Track a click on a product purchase link.
    Used for analytics and Grafana dashboards.
    """
    try:
        user_id = None
        if user_folder:
            user_folder_name = user_folder.split("/")[-1]
            user = db.query(User).filter(User.user_folder == user_folder_name).first()
            if user:
                user_id = user.id
        
        # Verify product exists
        product = db.query(Product).filter(Product.id == click.product_id).first()
        if not product:
            return JSONResponse(
                status_code=404,
                content={"error": "Product not found"}
            )
        
        # Create click record
        product_click = ProductClick(
            user_id=user_id,
            product_id=click.product_id,
            referrer=click.referrer or "unknown"
        )
        db.add(product_click)
        db.commit()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Click tracked",
                "click_id": product_click.id
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/image/{full_path:path}")
async def serve_image(full_path: str):
    """Serve an image file from data directory."""
    try:
        # Handle both cases - with or without "data/user_images/" prefix
        if full_path.startswith("data/user_images/"):
            relative_path = full_path.replace("data/user_images/", "", 1)
            image_path = IMAGES_DIR / relative_path
        elif full_path.startswith("user_"):
            image_path = IMAGES_DIR / full_path
        else:
            image_path = BASE_DIR / "data" / "user_images" / full_path
        
        if not image_path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": f"Image not found: {image_path}"}
            )
        
        return FileResponse(str(image_path))
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
