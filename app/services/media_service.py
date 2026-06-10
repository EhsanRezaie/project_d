import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import io

from app.core.logging import get_logger

logger = get_logger("media_service")

# Upload directories
CHAT_PHOTO_DIR = Path("uploads/chat/photo")
CHAT_VOICE_DIR = Path("uploads/chat/voice")

CHAT_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
CHAT_VOICE_DIR.mkdir(parents=True, exist_ok=True)


class MediaService:
    """Handle media uploads for chat"""

    MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_VOICE_SIZE = 2 * 1024 * 1024  # 2MB
    MAX_VOICE_DURATION = 120  # 2 minutes
    ALLOWED_IMAGE_FORMATS = ["JPEG", "PNG", "WEBP", "JPG"]

    @staticmethod
    async def save_photo(file_data: bytes, match_id: str, message_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Save photo message.
        Returns: (success, file_path, error_message)
        """
        # Check size
        if len(file_data) > MediaService.MAX_PHOTO_SIZE:
            return False, None, f"Photo too large. Max {MediaService.MAX_PHOTO_SIZE // (1024 * 1024)}MB"

        try:
            # Validate image
            image = Image.open(io.BytesIO(file_data))

            if image.format not in MediaService.ALLOWED_IMAGE_FORMATS:
                return False, None, f"Invalid format. Allowed: JPEG, PNG, WEBP"

            # Create directory
            match_dir = CHAT_PHOTO_DIR / match_id
            match_dir.mkdir(parents=True, exist_ok=True)

            # Save file
            file_path = match_dir / f"{message_id}.jpg"

            # Convert to RGB if needed
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

            return True, f"/uploads/chat/photo/{match_id}/{message_id}.jpg", None

        except Exception as e:
            logger.error(f"Failed to save photo: {e}")
            return False, None, "Invalid image file"

    @staticmethod
    async def save_voice(file_data: bytes, match_id: str, message_id: str, duration: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Save voice message.
        Returns: (success, file_path, error_message)
        """
        # Check size
        if len(file_data) > MediaService.MAX_VOICE_SIZE:
            return False, None, f"Voice message too large. Max {MediaService.MAX_VOICE_SIZE // (1024 * 1024)}MB"

        # Check duration
        if duration > MediaService.MAX_VOICE_DURATION:
            return False, None, f"Voice message too long. Max {MediaService.MAX_VOICE_DURATION} seconds"

        try:
            # Create directory
            match_dir = CHAT_VOICE_DIR / match_id
            match_dir.mkdir(parents=True, exist_ok=True)

            # Save file
            file_path = match_dir / f"{message_id}.mp3"

            with open(file_path, "wb") as f:
                f.write(file_data)

            return True, f"/uploads/chat/voice/{match_id}/{message_id}.mp3", None

        except Exception as e:
            logger.error(f"Failed to save voice: {e}")
            return False, None, "Failed to save voice message"

    @staticmethod
    async def delete_media(match_id: str, message_id: str, media_type: str) -> bool:
        """Delete media file"""
        if media_type == "photo":
            file_path = CHAT_PHOTO_DIR / match_id / f"{message_id}.jpg"
        elif media_type == "voice":
            file_path = CHAT_VOICE_DIR / match_id / f"{message_id}.mp3"
        else:
            return False

        if file_path.exists():
            file_path.unlink()
            return True
        return False