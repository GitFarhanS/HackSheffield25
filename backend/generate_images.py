import os
import io
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Dict, List

load_dotenv()

# Configuration paths - updated to match current structure
BASE_DIR = Path(__file__).parent.parent
USER_IMAGES_DIR = BASE_DIR / "data" / "user_images"

# Output image dimensions (9:16 aspect ratio)
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920  # 9:16 ratio


def resize_to_9_16(image: Image.Image) -> Image.Image:
    """
    Resize and crop image to 9:16 aspect ratio (1080x1920).
    Centers the image and crops/pads as needed.
    """
    target_ratio = 9 / 16  # 0.5625
    current_ratio = image.width / image.height
    
    if current_ratio > target_ratio:
        # Image is too wide - crop width
        new_width = int(image.height * target_ratio)
        left = (image.width - new_width) // 2
        image = image.crop((left, 0, left + new_width, image.height))
    elif current_ratio < target_ratio:
        # Image is too tall - crop height
        new_height = int(image.width / target_ratio)
        top = (image.height - new_height) // 2
        image = image.crop((0, top, image.width, top + new_height))
    
    # Resize to target dimensions
    image = image.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.Resampling.LANCZOS)
    
    return image

# Initialize Google GenAI client
api_key = os.getenv("IMAGE_API_KEY")
if not api_key:
    print("Warning: IMAGE_API_KEY not set - image generation will be skipped")
    client = None
else:
    client = genai.Client(api_key=api_key)
    print("✓ GenAI client initialized with IMAGE_API_KEY")


def generate_clothing_image_for_angle(
    user_folder_path: Path,
    product_image_path: Path,
    angle: str,
    product_index: int
) -> Optional[str]:
    """
    Generate an image of the user wearing the specified clothing item from a specific angle.
    
    Args:
        user_folder_path: Path to the user's folder (e.g., data/user_images/user_123)
        product_image_path: Path to the product image
        angle: One of 'front', 'side', 'back'
        product_index: Index of the product (1-based)
        
    Returns:
        Path to the generated image file, or None if generation failed
    """
    if not client:
        return None
    
    # Check if images exist - try both .jpg and .png extensions
    user_angle_path = None
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
        test_path = user_folder_path / f"{angle}{ext}"
        if test_path.exists():
            user_angle_path = test_path
            break
    
    if not user_angle_path:
        print(f"   User {angle} image not found (tried .jpg, .jpeg, .png): {user_folder_path}")
        return None
    if not product_image_path.exists():
        print(f"   Product image not found: {product_image_path}")
        return None
        
    try:
        # Load images using PIL (can be passed directly to Gemini)
        user_image = Image.open(user_angle_path)
        clothing_image = Image.open(product_image_path)
        
        # Create the prompt
        angle_desc = {
            'front': 'front view',
            'side': 'side profile view',
            'back': 'back view'
        }.get(angle, angle)
        
        prompt = (
            f"Take these 2 images ({angle_desc} of the person, and the clothing item) "
            f"and generate a realistic image of the person wearing this clothing item from the {angle_desc}. "
            f"Make sure the clothing fits naturally on the person and looks realistic. Make it in a 9:16 aspect ratio and centred towards the person."
        )
        
        print(f"   Generating {angle} view...")
        
        # Generate the image using GenAI
        # Use gemini-2.5-flash-image for image generation/editing
        # Pass images directly (PIL Images are automatically converted by the SDK)
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                user_image,      # User from specific angle
                clothing_image,  # Clothing item
                prompt           # Place text prompt after images as per documentation
            ]
        )
        
        # Create output directory
        output_dir = user_folder_path / "combined_images"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean product name for filename
        product_name = product_image_path.stem.replace(" ", "_")[:50]  # Limit length
        
        count = 0
        saved_path = None
        
        # Process response parts - access via candidates[0].content.parts
        parts = []
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts = candidate.content.parts
        
        for part in parts:
            if hasattr(part, 'text') and part.text:
                print(f"   Response text: {part.text[:100]}...")
            elif hasattr(part, 'inline_data') and part.inline_data is not None:
                # Save the generated image from inline_data bytes
                if count == 0:
                    output_path = output_dir / f"product_{product_index}_{angle}.jpg"
                else:
                    output_path = output_dir / f"product_{product_index}_{angle}_{count}.jpg"
                
                # Get image bytes from inline_data.data
                image_data = part.inline_data.data
                generated_image = Image.open(io.BytesIO(image_data))
                
                # Resize to 9:16 aspect ratio
                generated_image = resize_to_9_16(generated_image)
                
                generated_image.save(str(output_path), 'JPEG', quality=95)
                print(f"   ✓ Generated image saved to: {output_path.name} ({OUTPUT_WIDTH}x{OUTPUT_HEIGHT})")
                saved_path = str(output_path)
                count += 1
        
        if count == 0:
            print(f"   No image generated in response")
        
        return saved_path
        
    except Exception as e:
        print(f"   Error generating {angle} view: {e}")
        return None


def generate_all_angles_for_product(
    user_folder_path: Path,
    product_image_path: Path,
    product_index: int
) -> Dict[str, Optional[str]]:
    """
    Generate combined images for all angles (front, side, back) for a single product.
    
    Returns:
        Dictionary mapping angle to generated image path
    """
    results = {}
    
    for angle in ['front', 'side', 'back']:
        print(f"Generating {angle} view for product {product_index}...")
        result = generate_clothing_image_for_angle(
            user_folder_path,
            product_image_path,
            angle,
            product_index
        )
        results[angle] = result
    
    return results


def generate_combined_images_for_all_products(user_folder_path: str) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Generate combined images for all products in the user's folder.
    
    Args:
        user_folder_path: Path to user folder (e.g., "data/user_images/user_123")
        
    Returns:
        Dictionary mapping product index to angle results
    """
    if not client:
        print("GenAI client not initialized - skipping image generation")
        return {}
    
    user_path = Path(user_folder_path)
    product_images_dir = user_path / "products" / "product_images"
    
    if not product_images_dir.exists():
        print(f"No product images found in {product_images_dir}")
        return {}
    
    # Get all product images - handle jpg, jpeg, and png
    product_images = []
    for pattern in ["product_*.jpg", "product_*.jpeg", "product_*.png", "product_*.JPG", "product_*.JPEG", "product_*.PNG"]:
        product_images.extend(product_images_dir.glob(pattern))
    product_images = sorted(product_images)
    
    if not product_images:
        print("No product images found")
        return {}
    
    print(f"Found {len(product_images)} product images. Generating combined images...")
    
    all_results = {}
    
    for i, product_image_path in enumerate(product_images, 1):
        print(f"\nProcessing product {i}: {product_image_path.name}")
        results = generate_all_angles_for_product(user_path, product_image_path, i)
        all_results[str(i)] = results
    
    return all_results


if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_images.py <user_folder_path>")
        print("Example: python generate_images.py data/user_images/user_123")
        sys.exit(1)
    
    user_folder = sys.argv[1]
    
    try:
        results = generate_combined_images_for_all_products(user_folder)
        print("\n" + "=" * 60)
        print("Image Generation Complete!")
        print("=" * 60)
        
        total_generated = 0
        for product_id, angles in results.items():
            successful = [a for a, p in angles.items() if p]
            total_generated += len(successful)
            if successful:
                print(f"Product {product_id}: {', '.join(successful)}")
        
        print(f"\nTotal images generated: {total_generated}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
