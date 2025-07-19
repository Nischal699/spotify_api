from fastapi import APIRouter, WebSocket, WebSocketDisconnect , Depends
from app.core.manager_instance import manager
from app.database import get_db
from sqlalchemy.orm import Session


router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str,db: Session = Depends(get_db)):
    await manager.connect(user_id , websocket)
    print(f"User {user_id} connected! Users: {manager.get_online_users()}")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "get_users":
                await websocket.send_text(f"Online Users: {manager.get_online_users()}")
            else:
                message = f"User {user_id}: {data}"
                await manager.send_broadcast(message, sender_id=user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"User {user_id} disconnected.")
