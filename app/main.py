from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.models import user as user_model, track as track_model, like as like_model
from app.schemas import user as user_schema, track as track_schema , like as like_schema 
from app.database import get_db, Base, engine
from passlib.context import CryptContext
from app.api.endpoints import auth , tracks, likes , users , music_file
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

# Include routers for different endpoints

app.include_router(auth.router)
app.include_router(likes.router)
app.include_router(tracks.router)
app.include_router(users.router)
app.include_router(music_file.router)

# Mount static directory so files are accessible via /music_files/filename
app.mount("/music_files", StaticFiles(directory="app/static/music_files"), name="music_files")
