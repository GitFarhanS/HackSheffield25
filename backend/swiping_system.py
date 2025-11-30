"""
Tinder-style swiping system for clothing items.
Handles like/dislike actions and stores user preferences using PostgreSQL.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

try:
    from backend.models import User, Product, Swipe, LikedProduct
except ImportError:
    from models import User, Product, Swipe, LikedProduct

try:
    from backend.database import get_db
except ImportError:
    from database import get_db

# Base directory
BASE_DIR = Path(__file__).parent.parent
USER_IMAGES_DIR = BASE_DIR / "data" / "user_images"


class SwipingSystem:
    """Manages the swiping interface and liked photos storage."""
    
    def __init__(self, user_folder: str, db: Session):
        """
        Initialize the swiping system for a user.
        
        Args:
            user_folder: User folder name (e.g., "user_1764460714")
            db: Database session
        """
        self.user_folder = user_folder
        self.db = db
        self.user_path = USER_IMAGES_DIR / user_folder
        self.combined_images_dir = self.user_path / "combined_images"
        self.liked_photos_dir = self.user_path / "liked_photos"
        
        # Ensure liked_photos directory exists
        self.liked_photos_dir.mkdir(parents=True, exist_ok=True)
        
        # Get or create user in database
        self.user = db.query(User).filter(User.user_folder == user_folder).first()
        if not self.user:
            self.user = User(user_folder=user_folder)
            db.add(self.user)
            db.commit()
            db.refresh(self.user)
    
    def get_products(self) -> List[Dict]:
        """
        Get all products with their combined images for swiping.
        Uses products.json to correctly map product numbers to database IDs.
        
        Returns:
            List of product dictionaries with image paths and metadata
        """
        products = []
        
        # Read products.json which has the correct mapping
        products_json_path = self.user_path / "products" / "products.json"
        if not products_json_path.exists():
            print(f"   ⚠️ products.json not found at {products_json_path}")
            return []
        
        try:
            import json
            with open(products_json_path, 'r') as f:
                saved_products = json.load(f)
        except Exception as e:
            print(f"   ⚠️ Error reading products.json: {e}")
            return []
        
        # Find all product combined images
        if not self.combined_images_dir.exists():
            return []
        
        # Group images by product number (from filename) - handle both jpg and png
        product_images = {}
        for pattern in ["product_*_*.jpg", "product_*_*.jpeg", "product_*_*.png"]:
            for img_file in sorted(self.combined_images_dir.glob(pattern)):
                # Parse filename: product_1_front.jpg
                parts = img_file.stem.split("_")
                if len(parts) >= 3:
                    try:
                        product_num = int(parts[1])
                        angle = parts[2]
                        
                        if product_num not in product_images:
                            product_images[product_num] = {}
                        product_images[product_num][angle] = str(img_file)
                    except ValueError:
                        continue
        
        # Match products from products.json with their images
        for idx, saved_product in enumerate(saved_products, 1):
            # Get database product ID from saved product
            db_product_id = saved_product.get("db_product_id")
            
            # Get images for this product number (1-indexed)
            images = product_images.get(idx, {})
            
            # Try to get fresh data from database, fallback to saved data
            db_product = None
            if db_product_id:
                db_product = self.db.query(Product).filter(Product.id == db_product_id).first()
            
            products.append({
                "product_id": db_product_id or idx,
                "db_product_id": db_product_id,
                "title": db_product.title if db_product else saved_product.get("title", "Unknown"),
                "price": db_product.price if db_product else saved_product.get("price", "N/A"),
                "source": db_product.source if db_product else saved_product.get("source", ""),
                "rating": db_product.rating if db_product else saved_product.get("rating"),
                "reviews": db_product.reviews if db_product else saved_product.get("reviews"),
                "product_link": db_product.product_link if db_product else saved_product.get("product_link", ""),
                "thumbnail": db_product.thumbnail if db_product else saved_product.get("thumbnail", ""),
                "product_type": db_product.product_type if db_product else saved_product.get("product_type"),
                "images": {
                    "front": images.get("front"),
                    "side": images.get("side"),
                    "back": images.get("back")
                }
            })
        
        return products
    
    def swipe(self, product_id: int, liked: bool) -> Dict:
        """
        Record a swipe action.
        
        Args:
            product_id: The product database ID being swiped
            liked: True for right swipe (like), False for left (dislike)
            
        Returns:
            Updated swipe status
        """
        # Check if product exists
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"error": "Product not found"}
        
        # Check if already swiped
        existing_swipe = self.db.query(Swipe).filter(
            and_(Swipe.user_id == self.user.id, Swipe.product_id == product_id)
        ).first()
        
        if existing_swipe:
            # Update existing swipe
            existing_swipe.liked = liked
        else:
            # Create new swipe
            swipe = Swipe(user_id=self.user.id, product_id=product_id, liked=liked)
            self.db.add(swipe)
        
        # If liked, also add to liked_products
        if liked:
            existing_liked = self.db.query(LikedProduct).filter(
                and_(LikedProduct.user_id == self.user.id, LikedProduct.product_id == product_id)
            ).first()
            
            if not existing_liked:
                liked_product = LikedProduct(user_id=self.user.id, product_id=product_id)
                self.db.add(liked_product)
                
                # Copy images to liked_photos folder
                self._save_liked_product(product)
        
        self.db.commit()
        
        # Get updated stats
        total_swipes = self.db.query(Swipe).filter(Swipe.user_id == self.user.id).count()
        total_liked = self.db.query(Swipe).filter(
            and_(Swipe.user_id == self.user.id, Swipe.liked == True)
        ).count()
        total_disliked = self.db.query(Swipe).filter(
            and_(Swipe.user_id == self.user.id, Swipe.liked == False)
        ).count()
        
        products = self.get_products()
        remaining = len(products) - total_swipes
        
        return {
            "success": True,
            "liked": liked,
            "product_id": product_id,
            "total_liked": total_liked,
            "total_disliked": total_disliked,
            "completed": remaining <= 0,
            "remaining": max(0, remaining)
        }
    
    def _save_liked_product(self, product: Product):
        """Save liked product images and metadata to liked_photos folder."""
        product_id = product.id
        product_dir = self.liked_photos_dir / f"product_{product_id}"
        product_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the product data with image paths (uses products.json for correct mapping)
        products = self.get_products()
        
        found = False
        for p in products:
            if p["db_product_id"] == product_id:
                found = True
                # Copy each available angle image
                for angle in ["front", "side", "back"]:
                    src_path_str = p.get("images", {}).get(angle)
                    if src_path_str:
                        src_path = Path(src_path_str)
                        if src_path.exists():
                            dest = product_dir / f"{angle}.jpg"
                            try:
                                shutil.copy2(src_path, dest)
                                print(f"   ✓ Copied {angle} image for product {product_id} ({p.get('title', '')[:30]})")
                            except Exception as e:
                                print(f"   ⚠️ Failed to copy {angle} image: {e}")
                        else:
                            print(f"   ⚠️ Source image not found for {angle}: {src_path}")
                    else:
                        print(f"   ℹ️ No {angle} image available for product {product_id}")
                break
        
        if not found:
            print(f"   ⚠️ Product {product_id} not found in products.json - cannot copy images")
    
    def get_liked_products(self) -> List[Dict]:
        """
        Get all liked products with their metadata and images.
        Always returns products even if some images are missing.
        
        Returns:
            List of liked product data
        """
        liked_products = []
        
        # Get liked products from database
        liked_records = self.db.query(LikedProduct).filter(
            LikedProduct.user_id == self.user.id
        ).all()
        
        for liked_record in liked_records:
            product = liked_record.product
            if not product:
                continue
            
            # Get image paths - handle both jpg and png
            product_dir = self.liked_photos_dir / f"product_{product.id}"
            images = {"front": None, "side": None, "back": None}
            
            if product_dir.exists():
                def find_image(angle):
                    """Find image with any extension (jpg, jpeg, png)"""
                    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                        img_path = product_dir / f"{angle}{ext}"
                        if img_path.exists():
                            # Return relative path for API
                            return f"{self.user_folder}/liked_photos/product_{product.id}/{angle}{ext}"
                    return None
                
                images = {
                    "front": find_image("front"),
                    "side": find_image("side"),
                    "back": find_image("back")
                }
            
            # Also check combined_images as fallback
            if not any(images.values()):
                all_products = self.get_products()
                for p in all_products:
                    if p["db_product_id"] == product.id:
                        # Use combined images as fallback
                        for angle in ["front", "side", "back"]:
                            if p.get("images", {}).get(angle):
                                # Extract relative path from full path
                                full_path = p["images"][angle]
                                if self.user_folder in full_path:
                                    images[angle] = full_path.split(f"{self.user_folder}/")[-1]
                                    images[angle] = f"{self.user_folder}/{images[angle]}"
                        break
            
            liked_products.append({
                "product_id": product.id,
                "title": product.title,
                "price": product.price,
                "source": product.source,
                "rating": product.rating,
                "reviews": product.reviews,
                "product_link": product.product_link,
                "thumbnail": product.thumbnail,
                "product_type": product.product_type,
                "liked_at": liked_record.liked_at.isoformat() if liked_record.liked_at else None,
                "images": images,
                "has_images": any(images.values())
            })
        
        return liked_products
    
    def get_swipe_status(self) -> Dict:
        """Get current swiping status."""
        products = self.get_products()
        
        total_swipes = self.db.query(Swipe).filter(Swipe.user_id == self.user.id).count()
        liked_count = self.db.query(Swipe).filter(
            and_(Swipe.user_id == self.user.id, Swipe.liked == True)
        ).count()
        disliked_count = self.db.query(Swipe).filter(
            and_(Swipe.user_id == self.user.id, Swipe.liked == False)
        ).count()
        
        return {
            "total_products": len(products),
            "swiped": total_swipes,
            "liked_count": liked_count,
            "disliked_count": disliked_count,
            "remaining": len(products) - total_swipes,
            "completed": total_swipes >= len(products),
            "current_index": total_swipes
        }
    
    def reset_swipes(self):
        """Reset all swipe data for this user."""
        # Delete swipes
        self.db.query(Swipe).filter(Swipe.user_id == self.user.id).delete()
        
        # Delete liked products
        self.db.query(LikedProduct).filter(LikedProduct.user_id == self.user.id).delete()
        
        self.db.commit()
        
        # Clear liked photos folder
        if self.liked_photos_dir.exists():
            shutil.rmtree(self.liked_photos_dir)
            self.liked_photos_dir.mkdir(parents=True, exist_ok=True)
        
        return {"success": True, "message": "Swipe data reset"}
    
    def get_next_product(self) -> Optional[Dict]:
        """Get the next product to swipe on."""
        products = self.get_products()
        
        # Get already swiped product IDs
        swiped_product_ids = {
            swipe.product_id 
            for swipe in self.db.query(Swipe).filter(Swipe.user_id == self.user.id).all()
        }
        
        # Find first unswiped product
        for product in products:
            if product["product_id"] not in swiped_product_ids:
                return product
        
        return None  # All products swiped
