from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Base User schema (shared fields)
class UserBase(BaseModel):
    email: str

# User registration schema (expects password)
class UserCreate(UserBase):
    password: str
    role: Optional[str] = 'user'  # Default role is 'user'
    is_active: Optional[bool] = True  # Default to active user

# User response schema (sent to frontend)
class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# User login schema (login request payload)
class UserLogin(BaseModel):
    email: str
    password: str

# User response schema for showing user details
class ShowUser(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# User update schema (for updating user details)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

    class Config:
        orm_mode = True
