from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class AlbumRating(Base):
    __tablename__ = 'album_ratings'

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey('albums.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    user_score = Column(Integer)  # Оценка пользователя (0-100)
    critic_score = Column(Integer)  # Оценка критика (0-100)