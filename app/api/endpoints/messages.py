from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.message import Message

router = APIRouter(
    prefix="/messages",  # URL prefix for all routes in this router
    tags=["Messages"]  # Tags for documentation purposes
)

@router.put("/mark-seen/{message_id}")
def mark_message_seen(message_id: int, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if message:
        message.is_seen = True
        db.commit()
        return {"message": "Message marked as seen"}
    return {"error": "Message not found"}
