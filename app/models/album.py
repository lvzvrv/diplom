from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from .user import User  # Импортируем User для связи
from ..database import Base


class Album(Base):
    __tablename__ = 'albums'

    id = Column(Integer, primary_key=True, index=True)
    album_title = Column(String(255), nullable=False)
    artist_name = Column(String(255), nullable=False)
    release_date = Column(Date)
    cover_url = Column(String(512))
    genre = Column(String(100))
    created_at = Column(Date, server_default='now()')

    # Новые поля для хранения средних оценок
    user_score = Column(Float, default=0.0)  # Средняя оценка пользователей
    critic_score = Column(Float, default=0.0)  # Средняя оценка критиков

    # Связь с пользователями, которые оценили альбом
    ratings = relationship("AlbumRating", back_populates="album")


class AlbumRating(Base):
    __tablename__ = 'album_ratings'

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey('albums.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    user_score = Column(Integer)  # Оценка пользователя (0-100)
    critic_score = Column(Integer)  # Оценка критика (0-100)

    # Связи
    album = relationship("Album", back_populates="ratings")
    user = relationship("User")