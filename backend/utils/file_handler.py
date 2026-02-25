import os
import uuid
from pathlib import Path
from utils.config import settings

def ensure_upload_dir():
    """Create upload directory if it doesn't exist"""
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

def save_uploaded_file(file_content: bytes, original_filename: str) -> str:
    """
    Save uploaded file and return the path
    
    Args:
        file_content: File bytes
        original_filename: Original filename
        
    Returns:
        Path to saved file
    """
    ensure_upload_dir()
    
    # Generate unique filename
    file_extension = Path(original_filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path

def delete_file(file_path: str):
    """Delete a file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed"""
    return Path(filename).suffix.lower() in settings.ALLOWED_EXTENSIONS