# schemas/message.py
from typing import Optional, Dict
from pydantic import BaseModel
from datetime import datetime

class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime
    is_delivered: bool
    is_seen: bool
    reactions: Dict[str, int] = {}

    class Config:
        orm_mode = True
