from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, File

# Base Track schema (for shared fields)
class TrackBase(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = None  # seconds 
    file_url: Optional[str] = None  # URL to the track file 


# Schema for creating a track (when admin uploads track)
class TrackCreate(TrackBase):
    file_url: str  # URL to the track file

    class Config:
        from_attributes = True

# Schema for returning track data in API response
class TrackOut(TrackBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
