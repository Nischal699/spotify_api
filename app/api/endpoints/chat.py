from fastapi.concurrency import run_in_threadpool
from fastapi import WebSocket, APIRouter, Depends
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
            receiver_id = data.get("receiver_id")
            message = data.get("message")

            if receiver_id is None or message is None:
                await websocket.send_text("Error: 'receiver_id' and 'message' must be provided.")
                continue

            # Save message to DB in threadpool
            def save_message():
                try:
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
                except Exception as e:
                    db.rollback()
                    print(f"DB Save error: {e}")
                    raise e

            await run_in_threadpool(save_message)

            await manager.send_personal_message(f"{user_id}: {message}", receiver_id)

    except Exception as e:
        print(f"Disconnecting user {user_id}. Error: {e}")
        manager.disconnect(user_id)
        await manager.send_broadcast(f"📢 User {user_id} has disconnected.", sender_id=user_id)
