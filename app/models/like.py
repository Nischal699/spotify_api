from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    liked_at = Column(DateTime, default=datetime.utcnow)

    # Optional relationships (to easily fetch related data)
    user = relationship("User", backref="likes")
    track = relationship("Track", backref="likes")

    __table_args__ = (UniqueConstraint('user_id', 'track_id', name='_user_track_uc'),)

