from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True) 
    password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(String, default=datetime.utcnow)  # Use appropriate datetime type if needed

