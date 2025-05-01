from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime


class AlbumReview(Base):
    __tablename__ = 'album_reviews'

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey('albums.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    review_text = Column(String(1000))
    score = Column(Integer)  # 1-100
    created_at = Column(DateTime, default=datetime.utcnow)
    is_critic_review = Column(Boolean, default=False)