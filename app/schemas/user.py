from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Base User schema (shared fields)
class UserBase(BaseModel):
    username: str
    email: EmailStr

# User registration schema (expects password)
class UserCreate(UserBase):
    password: str

# User response schema (sent to frontend)
class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# User login schema (login request payload)
class UserLogin(BaseModel):
    email: EmailStr
    password: str
