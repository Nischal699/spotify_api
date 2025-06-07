from pydantic import BaseModel
from datetime import datetime

# Base Like schema
class LikeBase(BaseModel):
    user_id: int
    track_id: int

# Schema for creating a like
class LikeCreate(LikeBase):
    pass

# Schema for returning like data
class LikeOut(LikeBase):
    id: int
    liked_at: datetime

    class Config:
        orm_mode = True
