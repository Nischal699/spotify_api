from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from fastapi import Depends
from app.core.security import get_current_user
from app.schemas import user as user_schema

# Create a new router for music file-related endpoints
router = APIRouter(
    prefix="/music",  # URL prefix for all routes in this router
    tags=["Music Files"]  # Tags for documentation purposes
)

@router.post("/upload-music/")
async def upload_music(file: UploadFile = File(...),current_user: user_schema.UserBase = Depends(get_current_user)):
    # Validate file type (optional)
    if not file.filename.endswith((".mp3", ".wav", ".ogg")):
        raise HTTPException(status_code=400, detail="Invalid file type")

    upload_folder = "app/static/music_files"
    file_location = os.path.join(upload_folder, file.filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/music_files/{file.filename}"
    return {"filename": file.filename, "url": file_url}
