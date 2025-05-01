from .base import Base
from .user import User
from .album import Album
from .album_review import AlbumReview
from .album_rating import AlbumRating

# Инициализируем отношения после импорта всех моделей
from .relations import setup_relationships
setup_relationships()

__all__ = ['Base', 'User', 'Album']