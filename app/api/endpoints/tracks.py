from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import track as track_model
from app.schemas import track as track_schema


router = APIRouter(
    prefix="/tracks",  # URL prefix for all routes in this router
    tags=["Tracks"]  # Tags for documentation purposes
)

@router.post("/create_track", response_model=track_schema.TrackBase)
def create_track(request: track_schema.TrackBase, db: Session = Depends(get_db)):
    # Optional: check if track already exists
    existing_track = db.query(track_model.Track).filter(track_model.Track.title == request.title).first()
    if existing_track:
        raise HTTPException(status_code=400, detail="Track already exists")
    
    # Create a new track instance and add it to the database
    new_track = track_model.Track(
        title=request.title,
        artist=request.artist,
        album=request.album,
        duration=request.duration
    )
    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    return new_track