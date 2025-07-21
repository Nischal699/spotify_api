from typing import List
import os
import shutil
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import track as track_model
from app.schemas import track as track_schema , user as user_schema
from app.core.security import get_current_admin_user, get_current_user


router = APIRouter(
    prefix="/tracks",  # URL prefix for all routes in this router
    tags=["Tracks"]  # Tags for documentation purposes
)

UPLOAD_FOLDER = "app/static/music_files"
# Ensure the upload folder exists

@router.post("/", response_model=track_schema.TrackBase, dependencies=[Depends(get_current_admin_user)])
def create_track(
    title: str,
    artist: str,
    album: str | None = None,
    duration: str | None = None,
    music_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: user_schema.UserBase = Depends(get_current_user)
):
    existing_track = db.query(track_model.Track).filter(track_model.Track.title == title).first()
    if existing_track:
        raise HTTPException(status_code=400, detail="Track already exists")

    file_url = None
    if music_file:
        if not music_file.filename.endswith((".mp3", ".wav", ".ogg")):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        file_location = os.path.join(UPLOAD_FOLDER, music_file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(music_file.file, buffer)
        
        file_url = f"/music_files/{music_file.filename}"

    new_track = track_model.Track(
        title=title,
        artist=artist,
        album=album,
        duration=duration,
        file_url=file_url
    )
    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    return new_track

@router.get("/", response_model=List[track_schema.TrackBase], status_code=200)
def get_all_tracks(db: Session = Depends(get_db)):
    tracks = db.query(track_model.Track).all()
    return tracks


@router.get("/{id}", response_model=track_schema.TrackBase, status_code=200)
def get_track(id: int, db: Session = Depends(get_db)):
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
    if request.file_url:
        # If a new file URL is provided, update it
        track.file_url = request.file_url
    
    db.commit()
    db.refresh(track)
    return track

@router.delete("/{id}", status_code=204)
def delete_track(id: int, db: Session = Depends(get_db), current_user: user_schema.UserBase = Depends(get_current_user)):
    track = db.query(track_model.Track).filter(track_model.Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail=f'Track with id {id} not found')

    # Delete associated music file if it exists
    if track.file_url:
        file_path = os.path.join("app/static", track.file_url.strip("/"))
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(track)
    db.commit()
    return {"detail": f"Track with id {id} and associated file (if any) deleted successfully"}
