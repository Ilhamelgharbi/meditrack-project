from fastapi import UploadFile
from pathlib import Path
import shutil
from typing import Optional
from app.config.settings import settings

def save_uploaded_file(
    file: UploadFile | None,
    folder: str,
) -> Optional[Path]:
    """
    Save an uploaded file to disk and return its path.
    
    Args:
        file: FastAPI UploadFile
        folder: Subfolder inside uploads/ (e.g. 'audio', 'images')

    Returns:
        Path to saved file or None if file is not provided
    """
    if not file:
        return None

    # Use UPLOADS_PATH from config
    upload_dir = Path(settings.UPLOADS_PATH) / folder
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename

    with file_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    return file_path
