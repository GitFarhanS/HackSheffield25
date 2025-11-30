import requests
import json
import urllib.parse
import os
import io
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from sqlalchemy.orm import Session
from PIL import Image

try:
    from backend.models import Product
except ImportError:
    from models import Product

# Load environment variables
load_dotenv()

# -------------------------------------------
# CONFIGURATION
# -------------------------------------------
SERPAPI_KEY = os.getenv("SERPI_API")
SERPAPI_ENDPOINT = "https://serpapi.com/search"

# Headers for downloading images
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}


def download_image(image_url: str, save_path: Path, max_size: int = 512, quality: int = 85) -> bool:
    """
    Download an image from URL, compress it using Pillow, and save it.
    
    Args:
        image_url: URL of the image to download
        save_path: Path where to save the compressed image
        max_size: Maximum dimension (width or height) in pixels (default: 512)
        quality: JPEG quality 1-100 (default: 85)
    
    Returns True if successful, False otherwise.
    """
    if not image_url:
        return False
    
    try:
        # Download the image
        response = requests.get(image_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Open image with Pillow
        img = Image.open(io.BytesIO(response.content))
        
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
        img.save(save_path, 'JPEG', quality=quality, optimize=True)
        
        # Log compression stats
        original_size = len(response.content)
        compressed_size = save_path.stat().st_size
        reduction = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        print(f"   📦 Compressed: {original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB ({reduction:.0f}% reduction)")
        
        return True
    except Exception as e:
        print(f"   ⚠️  Failed to download/compress image: {e}")
        return False


def save_product_link(link: str, product_index: int, links_dir: Path) -> Path:
    """
    Save product link to a text file.
    Returns the path to the saved file.
    """
    link_file = links_dir / f"product_{product_index + 1}_link.txt"
    with open(link_file, 'w') as f:
        f.write(link)
    return link_file


def search_google_shopping(
    search_query: str, 
    user_folder_path: str = None, 
    num_results: int = 5,
    db: Optional[Session] = None,
    product_type: Optional[str] = None
):
    """
    Search Google Shopping via SerpApi for products and optionally save images and links.
    
    Args:
        search_query: Search query string
        user_folder_path: Optional path to user folder where products should be saved
        num_results: Number of results to return (default: 5)
    
    Returns:
        List of product dictionaries with keys: brand, title, price, link, image, local_image
    """
    if not SERPAPI_KEY:
        print("❌ SERPI_API key not found in environment variables")
        return []
    
    print(f"🔎 Searching Google Shopping for: '{search_query}'...")
    
    # Build the API request parameters
    params = {
        "engine": "google_shopping",
        "q": search_query,
        "api_key": SERPAPI_KEY,
        "num": num_results * 2,  # Request more to account for filtering
        "google_domain": "google.co.uk",  # Search via UK Google
        "gl": "uk",  # Country: UK
        "hl": "en",  # Language: English
        # "tbs": "mr:1,merchagg:m113940428",  # Optional: Filter to House of Fraser only
    }

    try:
        response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching from SerpApi: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing API response: {e}")
        return []
    
    # Check for API errors
    if "error" in data:
        print(f"❌ SerpApi error: {data['error']}")
        return []

    products = []
    
    # Set up product directories if user_folder_path is provided
    images_dir = None
    links_dir = None
    if user_folder_path:
        products_dir = Path(user_folder_path) / "products"
        images_dir = products_dir / "product_images"
        links_dir = products_dir / "product_links"
        
        # Create directories if they don't exist
        images_dir.mkdir(parents=True, exist_ok=True)
        links_dir.mkdir(parents=True, exist_ok=True)
        print(f"   📁 Saving products to: {products_dir}")
    
    # Parse shopping results
    shopping_results = data.get("shopping_results", [])
    print(f"   Found {len(shopping_results)} products from Google Shopping")
    
    for index, item in enumerate(shopping_results):
        if len(products) >= num_results:
            break
            
        try:
            # Extract product details from SerpApi response
            # See: https://serpapi.com/google-shopping-api
            title = item.get("title", "Unknown Product")
            product_id = item.get("product_id", "")
            
            # Get the Google Shopping product link
            product_link = item.get("product_link", "")
            
            # thumbnail is the main image URL
            image_url = item.get("thumbnail", "")
            
            # Price extraction
            price = item.get("price", "")
            if not price:
                extracted_price = item.get("extracted_price")
                if extracted_price:
                    price = f"£{extracted_price}"
            
            # Extract source (retailer) and other metadata
            source = item.get("source", "")
            
            # Skip items without essential data
            if not title or not product_link:
                continue
            
            # Download and save image if user_folder_path is provided
            local_image_path = None
            if images_dir and image_url:
                # Clean filename (remove invalid characters)
                safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
                image_filename = f"product_{len(products) + 1}_{safe_name}.jpg".replace(' ', '_')
                image_path = images_dir / image_filename
                
                if download_image(image_url, image_path):
                    local_image_path = str(image_path)
                    print(f"   💾 Saved image: {image_filename}")
            
            # Save product link if user_folder_path is provided
            if links_dir:
                link_file = save_product_link(product_link, len(products), links_dir)
                print(f"   💾 Saved link: {link_file.name}")
            
            # Save to database if db session provided
            # Create unique product_id per user session to ensure proper image mapping
            db_product_id = None
            if db:
                # Extract user folder for unique product ID
                user_folder_name = ""
                if user_folder_path:
                    user_folder_name = Path(user_folder_path).name
                
                # Generate session-unique product_id: original_id + user_folder
                session_product_id = f"{product_id}_{user_folder_name}" if user_folder_name else product_id
                
                # Always create new product for this user's search session
                # This ensures db_product_id matches the image numbering (product_1, product_2, etc.)
                db_product = Product(
                    product_id=session_product_id,  # Unique per user session
                    title=title,
                    price=price,
                    extracted_price=item.get("extracted_price"),
                    old_price=item.get("old_price"),
                    product_link=product_link,
                    thumbnail=image_url,
                    source=source,
                    source_icon=item.get("source_icon"),
                    rating=item.get("rating"),
                    reviews=item.get("reviews"),
                    snippet=item.get("snippet"),
                    delivery=item.get("delivery"),
                    tag=item.get("tag"),
                    product_type=product_type  # Set from preferences
                )
                db.add(db_product)
                db.commit()
                db.refresh(db_product)
                db_product_id = db_product.id
            
            # Add to results list
            products.append({
                "product_id": product_id,  # API product_id
                "db_product_id": db_product_id,  # Database ID
                "title": title,
                "price": price,
                "extracted_price": item.get("extracted_price"),
                "old_price": item.get("old_price"),
                "product_link": product_link,
                "thumbnail": image_url,
                "local_image": local_image_path,
                "source": source,
                "source_icon": item.get("source_icon"),
                "rating": item.get("rating"),
                "reviews": item.get("reviews"),
                "snippet": item.get("snippet"),
                "delivery": item.get("delivery"),
                "tag": item.get("tag"),
                "product_type": product_type,
            })
            
            print(f"   ✓ [{len(products)}] {title[:50]}... - {price}")
            
        except Exception as e:
            print(f"   ⚠️  Error processing product {index + 1}: {e}")
            continue
    
    print(f"   📦 Retrieved {len(products)} products")
    
    # Save products.json to user folder for the swiping system
    if user_folder_path and products:
        products_json_path = Path(user_folder_path) / "products" / "products.json"
        products_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(products_json_path, 'w') as f:
            json.dump(products, f, indent=2)
        print(f"   💾 Saved products.json to {products_json_path}")
    
    return products


# Alias for backward compatibility with main.py
def scrape_house_of_fraser(
    search_query: str, 
    user_folder_path: str = None,
    db: Optional[Session] = None,
    preferences_data: Optional[dict] = None
):
    """
    Backward-compatible function name. Now uses Google Shopping API via SerpApi.
    Extracts product_type from preferences if provided.
    """
    # Extract product_type from preferences (first clothing_type)
    product_type = None
    if preferences_data and preferences_data.get("clothing_types"):
        clothing_types = preferences_data["clothing_types"]
        if isinstance(clothing_types, list) and len(clothing_types) > 0:
            product_type = clothing_types[0]  # Use first type as primary
    
    return search_google_shopping(
        search_query, 
        user_folder_path,
        db=db,
        product_type=product_type
    )


# -------------------------------------------
# MAIN EXECUTION
# -------------------------------------------
if __name__ == "__main__":
    # Example Query
    query = "formal shirt men"
    
    print("=" * 60)
    print("Google Shopping API via SerpApi - Product Search")
    print("=" * 60)
    
    results = search_google_shopping(query)
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    if results:
        for i, item in enumerate(results, 1):
            print(f"\n{i}. {item['title']}")
            if item.get('source'):
                print(f"   🏷️  Source: {item['source']}")
            print(f"   💰 Price: {item['price']}")
            if item.get('old_price'):
                print(f"   💸 Was: {item['old_price']}")
            if item.get('rating'):
                print(f"   ⭐ Rating: {item['rating']} ({item.get('reviews', 'N/A')} reviews)")
            if item.get('delivery'):
                print(f"   🚚 {item['delivery']}")
            print(f"   🔗 {item['product_link'][:100]}...")
            print(f"   🖼️  {item['thumbnail'][:80]}..." if item.get('thumbnail') else "   🖼️  No image")
            print("-" * 50)
            
        # Save to file
        with open("products.json", "w") as f:
            json.dump(results, f, indent=2)
            print("\n✅ Saved results to products.json")
    else:
        print("No products found. Check your SERPI_API key or try a different query.")
