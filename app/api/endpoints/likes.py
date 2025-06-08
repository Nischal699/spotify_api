from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database import get_db
from app.models import user as user_model, track as track_model, like as like_model
from app.schemas import user as user_schema, track as track_schema, like as like_schema
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix="/likes",  # URL prefix for all routes in this router
    tags=["Likes"],  # Tags for documentation purposes
)


@router.post("/create_like", response_model=like_schema.LikeOut)
def like_track(request: like_schema.LikeCreate, db: Session = Depends(get_db),current_user: user_schema.UserBase = Depends(get_current_user)):
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

@router.post("/unlike", response_model=like_schema.LikeOut)
def unlike_track(request: like_schema.LikeCreate, db: Session = Depends(get_db), current_user: user_schema.UserBase = Depends(get_current_user)):   
    # Check if user exists
    user_exist = db.query(user_model.User).filter(user_model.User.id == request.user_id).first()
    if not user_exist:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if track exists
    track_exist = db.query(track_model.Track).filter(track_model.Track.id == request.track_id).first()
    if not track_exist:
        raise HTTPException(status_code=404, detail="Track not found")

    # Find the like entry to remove
    like_entry = db.query(like_model.Like).filter(
        like_model.Like.user_id == request.user_id,
        like_model.Like.track_id == request.track_id
    ).first()

    if not like_entry:
        raise HTTPException(status_code=404, detail="Like not found")

    # Delete the like entry
    db.delete(like_entry)
    db.commit()

    return like_entry