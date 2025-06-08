from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import track as track_model
from app.schemas import track as track_schema , user as user_schema
from app.core.security import get_current_admin_user, get_current_user


router = APIRouter(
    prefix="/tracks",  # URL prefix for all routes in this router
    tags=["Tracks"]  # Tags for documentation purposes
)

@router.post("/", response_model=track_schema.TrackBase,dependencies=[Depends(get_current_admin_user)])
def create_track(request: track_schema.TrackBase, db: Session = Depends(get_db), current_user: user_schema.UserBase = Depends(get_current_user)):
    # Optional: check if track already exists
    existing_track = db.query(track_model.Track).filter(track_model.Track.title == request.title).first()
    if existing_track:
        raise HTTPException(status_code=400, detail="Track already exists")
    
    # Create a new track instance and add it to the database
    new_track = track_model.Track(
        title=request.title,
        artist=request.artist,
        album=request.album,
        duration=request.duration,
    )
    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    return new_track

@router.get("/{id}", response_model=track_schema.TrackBase, status_code=200)
def get_track(id: int, db: Session = Depends(get_db), current_user: user_schema.UserBase = Depends(get_current_user)):
    track = db.query(track_model.Track).filter(track_model.Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail=f'Track with id {id} not found')
    return track

@router.put("/{id}", response_model=track_schema.TrackBase, status_code=200)
def update_track(id: int, request: track_schema.TrackBase, db: Session = Depends(get_db), current_user: user_schema.UserBase = Depends(get_current_user)):
    track = db.query(track_model.Track).filter(track_model.Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail=f'Track with id {id} not found')
    
    # Update the track's details
    track.title = request.title
    track.artist = request.artist
    track.album = request.album
    track.duration = request.duration
    
    db.commit()
    db.refresh(track)
    return track

@router.delete("/{id}", status_code=204)
def delete_track(id: int, db: Session = Depends(get_db), current_user: user_schema.UserBase = Depends(get_current_user)):
    track = db.query(track_model.Track).filter(track_model.Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail=f'Track with id {id} not found')
    
    db.delete(track)
    db.commit()
    return {"detail": "Track deleted successfully"}