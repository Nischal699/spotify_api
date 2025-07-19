from typing import List
from app.schemas.message import MessageOut
from fastapi.concurrency import run_in_threadpool
from fastapi import WebSocket, APIRouter, Depends , Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.manager_instance import manager
from app.models.message import Message
from datetime import datetime

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await manager.connect(user_id, websocket)
    await manager.send_broadcast(f"📢 User {user_id} is now online!", sender_id=user_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "chat_message")

            # ✅ 1. Typing indicator
            if msg_type == "typing":
                receiver_id = data.get("receiver_id")
                if receiver_id is not None:
                    await manager.send_personal_message({
                    "type": "typing",
                    "sender_id": user_id,
                }, receiver_id)
                continue
            # ✅ 2. Chat message
            elif msg_type == "chat_message":
                receiver_id = data.get("receiver_id")
                message = data.get("message")

                if receiver_id is None or message is None:
                    await websocket.send_text("Error: 'receiver_id' and 'message' must be provided.")
                    continue

                # Save message in DB
                def save_message():
                    new_message = Message(
                        sender_id=user_id,
                        receiver_id=receiver_id,
                        content=message,
                        is_delivered=True,
                        timestamp=datetime.utcnow()
                    )
                    db.add(new_message)
                    db.commit()
                    db.refresh(new_message)
                    print(f"Message saved with id: {new_message.id}")

                await run_in_threadpool(save_message)

                msg_payload = {
                    "type": "chat_message",
                    "sender_id": user_id,
                    "receiver_id": receiver_id,
                    "message": message
                }

                await manager.send_personal_message(msg_payload, receiver_id)
                await websocket.send_json(msg_payload)

            elif msg_type == "mark_seen":
                sender_id = int(data.get("sender_id"))

                def mark_seen():
                    unseen_messages = db.query(Message).filter(
                        Message.sender_id == sender_id,
                        Message.receiver_id == user_id,
                        Message.is_seen == False
                    ).all()

                    for message in unseen_messages:
                        message.is_seen = True
                    db.commit()

                await run_in_threadpool(mark_seen)

                # Notify the original sender that their messages were seen
                await manager.send_personal_message({
                    "type": "seen_ack",
                    "receiver_id": user_id
                }, sender_id)

    except Exception as e:
        print(f"Disconnecting user {user_id}. Error: {e}")
        manager.disconnect(user_id)
        await manager.send_broadcast(f"📢 User {user_id} has disconnected.", sender_id=user_id)
        

@router.get("/history/", response_model=List[MessageOut])
def get_message_history(
    user_id: int,
    other_user_id: int,
    limit: int = Query(20),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    # ✅ Mark other_user's messages as seen
    mark_messages_seen(db, sender_id=other_user_id, receiver_id=user_id)
    
    messages = db.query(Message).filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp.desc()).offset(offset).limit(limit).all()

    return list(reversed(messages))  # oldest first

def mark_messages_seen(db: Session, sender_id: int, receiver_id: int):
    unseen_messages = db.query(Message).filter(
        Message.sender_id == sender_id,
        Message.receiver_id == receiver_id,
        Message.is_seen == False
    ).all()

    for message in unseen_messages:
        message.is_seen = True

    db.commit()