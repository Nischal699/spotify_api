from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.models import user as user_model, track as track_model, like as like_model
from app.schemas import user as user_schema, track as track_schema , like as like_schema 
from app.database import get_db, Base, engine
from passlib.context import CryptContext
from app.api.endpoints import auth , tracks, likes , users , chat , messages , websocket
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

# Include routers for different endpoints

app.include_router(auth.router)
app.include_router(likes.router)
app.include_router(tracks.router)
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(messages.router)
app.include_router(websocket.router)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # add your frontend port here too
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Mount static directory so files are accessible via /music_files/filename
app.mount("/music_files", StaticFiles(directory="app/static/music_files"), name="music_files")
