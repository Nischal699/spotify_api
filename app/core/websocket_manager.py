from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_personal_message(self, message: str, receiver_id: int):
        if receiver_id in self.active_connections:
            await self.active_connections[receiver_id].send_text(message)

    def get_online_users(self):
        return list(self.active_connections.keys())
    
    async def send_broadcast(self, message: str, sender_id: int):
        for uid, connection in self.active_connections.items():
            if uid != sender_id:
                await connection.send_text(message)

