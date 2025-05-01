from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime


class Album(Base):
    __tablename__ = 'albums'

    id = Column(Integer, primary_key=True, index=True)
    album_title = Column(String(255), nullable=False)
    artist_name = Column(String(255), nullable=False)
    release_date = Column(DateTime)
    cover_url = Column(String(512))
    genre = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    user_score = Column(Float, default=0.0)
    critic_score = Column(Float, default=0.0)

    # Уберем relationships здесь