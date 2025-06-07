from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import user as user_model, track as track_model, like as like_model
from app.schemas import user as user_schema, track as track_schema , like as like_schema 
from app.database import get_db, Base, engine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/create_user", response_model=user_schema.UserBase)
def create_user(request: user_schema.UserBase, db: Session = Depends(get_db)):
    # Optional: check if user already exists
    existing_user = db.query(user_model.User).filter(user_model.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password before storing it
    request.password = pwd_context.hash(request.password)

    # Create a new user instance and add it to the database

    new_user = user_model.User(
        username=request.username,
        email=request.email,
        password=request.password  # You should hash this before storing!
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/create_track", response_model=track_schema.TrackBase)
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

@app.post("/create_like", response_model=like_schema.LikeOut)
def like_track(request: like_schema.LikeCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user_exist = db.query(user_model.User).filter(user_model.User.id == request.user_id).first()
    if not user_exist:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if track exists
    track_exist = db.query(track_model.Track).filter(track_model.Track.id == request.track_id).first()
    if not track_exist:
        raise HTTPException(status_code=404, detail="Track not found")

    # Optional: check if this like already exists (to avoid duplicates)
    existing_like = db.query(like_model.Like).filter(
        like_model.Like.user_id == request.user_id,
        like_model.Like.track_id == request.track_id
    ).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="Already liked")

    # Create Like entry
    new_like = like_model.Like(
        user_id=request.user_id,
        track_id=request.track_id,
        liked_at=datetime.utcnow()
    )
    db.add(new_like)
    db.commit()
    db.refresh(new_like)

    return new_like
