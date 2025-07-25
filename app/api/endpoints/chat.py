from typing import List
from app.schemas.message import MessageOut
from fastapi.concurrency import run_in_threadpool
from fastapi import WebSocket, APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.manager_instance import manager
from app.models.message import Message, MessageReaction  # <- Import MessageReaction model here
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

            # ✅ 3. Mark messages as seen
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

                # Notify sender their messages were seen
                await manager.send_personal_message({
                    "type": "seen_ack",
                    "receiver_id": user_id
                }, sender_id)

            # ✅ 4. Add reaction
            elif msg_type == "add_reaction":
                message_id = data.get("message_id")
                emoji = data.get("emoji")
                if not message_id or not emoji:
                    await websocket.send_text("Error: 'message_id' and 'emoji' required for adding reaction.")
                    continue

                def add_reaction():
                    # Check if message exists
                    message_obj = db.query(Message).filter(Message.id == message_id).first()
                    if not message_obj:
                        raise HTTPException(status_code=404, detail="Message not found")

                    # Check if reaction exists for this user & message
                    existing_reaction = db.query(MessageReaction).filter_by(
                        message_id=message_id,
                        user_id=user_id,
                        emoji=emoji
                    ).first()
                    if existing_reaction:
                        return None  # Already reacted

                    reaction = MessageReaction(
                        message_id=message_id,
                        user_id=user_id,
                        emoji=emoji
                    )
                    db.add(reaction)
                    db.commit()
                    db.refresh(reaction)
                    return reaction

                reaction_obj = await run_in_threadpool(add_reaction)
                if reaction_obj is None:
                    continue  # Already reacted, no need to notify

                # Broadcast reaction update to sender & receiver
                msg_obj = db.query(Message).filter(Message.id == message_id).first()
                reaction_payload = {
                    "type": "reaction_update",
                    "message_id": message_id,
                    "user_id": user_id,
                    "emoji": emoji,
                    "action": "add"
                }
                # Notify sender and receiver of the message
                await manager.send_personal_message(reaction_payload, msg_obj.sender_id)
                await manager.send_personal_message(reaction_payload, msg_obj.receiver_id)

            # ✅ 5. Remove reaction
            elif msg_type == "remove_reaction":
                message_id = data.get("message_id")
                emoji = data.get("emoji")
                if not message_id or not emoji:
                    await websocket.send_text("Error: 'message_id' and 'emoji' required for removing reaction.")
                    continue

                def remove_reaction():
                    reaction = db.query(MessageReaction).filter_by(
                        message_id=message_id,
                        user_id=user_id,
                        emoji=emoji
                    ).first()
                    if reaction:
                        db.delete(reaction)
                        db.commit()
                        return True
                    return False

                removed = await run_in_threadpool(remove_reaction)
                if not removed:
                    continue  # No reaction found, nothing to do

                # Broadcast reaction removal
                msg_obj = db.query(Message).filter(Message.id == message_id).first()
                reaction_payload = {
                    "type": "reaction_update",
                    "message_id": message_id,
                    "user_id": user_id,
                    "emoji": emoji,
                    "action": "remove"
                }
                await manager.send_personal_message(reaction_payload, msg_obj.sender_id)
                await manager.send_personal_message(reaction_payload, msg_obj.receiver_id)

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
    # Mark other_user's messages as seen
    mark_messages_seen(db, sender_id=other_user_id, receiver_id=user_id)

    messages = db.query(Message).filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp.desc()).offset(offset).limit(limit).all()

    enriched_messages = []
    for msg in messages:
        # ✅ Aggregate reactions per emoji
        reactions = db.query(MessageReaction.emoji).filter_by(message_id=msg.id).all()
        reaction_counts = {}
        for emoji_row in reactions:
            emoji = emoji_row[0]
            reaction_counts[emoji] = reaction_counts.get(emoji, 0) + 1

        enriched_messages.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "is_delivered": msg.is_delivered,
            "is_seen": msg.is_seen,
            "reactions": reaction_counts  # ✅ Inject actual emoji reactions
        })

    return list(reversed(enriched_messages))


def mark_messages_seen(db: Session, sender_id: int, receiver_id: int):
    unseen_messages = db.query(Message).filter(
        Message.sender_id == sender_id,
        Message.receiver_id == receiver_id,
        Message.is_seen == False
    ).all()

    for message in unseen_messages:
        message.is_seen = True

    db.commit()
