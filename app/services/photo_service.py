import os
import uuid
import shutil
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import io

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("photo_service")

# Create upload directory if not exists
UPLOAD_DIR = Path("uploads/users")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class PhotoService:
    """Handle photo upload, validation, and storage"""
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_FORMATS = ["JPEG", "PNG", "WEBP"]
    MIN_WIDTH = 200
    MIN_HEIGHT = 200
    MAX_WIDTH = 5000
    MAX_HEIGHT = 5000
    
    @staticmethod
    async def validate_image(file_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image file.
        Returns: (is_valid, error_message)
        """
        # Check file size
        if len(file_data) > PhotoService.MAX_FILE_SIZE:
            return False, f"Image too large. Max {PhotoService.MAX_FILE_SIZE // (1024*1024)}MB"
        
        try:
            # Open and validate image
            image = Image.open(io.BytesIO(file_data))
            
            # Check format
            if image.format not in PhotoService.ALLOWED_FORMATS:
                return False, f"Invalid format. Allowed: {', '.join(PhotoService.ALLOWED_FORMATS)}"
            
            # Check dimensions
            width, height = image.size
            if width < PhotoService.MIN_WIDTH or height < PhotoService.MIN_HEIGHT:
                return False, f"Image too small. Minimum {PhotoService.MIN_WIDTH}x{PhotoService.MIN_HEIGHT}"
            
            if width > PhotoService.MAX_WIDTH or height > PhotoService.MAX_HEIGHT:
                return False, f"Image too large. Maximum {PhotoService.MAX_WIDTH}x{PhotoService.MAX_HEIGHT}"
            
            # Check aspect ratio (not too extreme)
            ratio = width / height
            if ratio > 3 or ratio < 0.33:
                return False, "Image aspect ratio too extreme. Use normal photos."
            
            return True, None
            
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False, "Invalid or corrupted image file"
    
    @staticmethod
    async def save_photo(user_id: str, photo_id: str, file_data: bytes) -> str:
        """
        Save photo to disk and return URL.
        """
        # Create user directory
        user_dir = UPLOAD_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = user_dir / f"{photo_id}.jpg"
        
        # Optimize image before saving
        image = Image.open(io.BytesIO(file_data))
        
        # Convert to RGB if needed (for PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        
        # Resize if too large (max 1200px)
        max_size = 1200
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Save as JPEG with 85% quality
        image.save(file_path, 'JPEG', quality=85, optimize=True)
        
        # Return URL
        return f"/uploads/users/{user_id}/{photo_id}.jpg"
    
    @staticmethod
    async def delete_photo(user_id: str, photo_id: str) -> bool:
        """Delete photo from disk"""
        file_path = UPLOAD_DIR / str(user_id) / f"{photo_id}.jpg"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    @staticmethod
    async def get_photo_url(user_id: str, photo_id: str) -> str:
        """Get photo URL"""
        return f"/uploads/users/{user_id}/{photo_id}.jpg"