from sqlalchemy.orm import relationship


def setup_relationships():
    from .user import User
    from .album import Album
    from .album_review import AlbumReview
    from .album_rating import AlbumRating

    # Настраиваем отношения для User
    User.reviews = relationship("AlbumReview", back_populates="user")
    User.ratings = relationship("AlbumRating", back_populates="user")

    # Настраиваем отношения для Album
    Album.reviews = relationship("AlbumReview", back_populates="album")
    Album.ratings = relationship("AlbumRating", back_populates="album")

    # Настраиваем отношения для AlbumReview
    AlbumReview.user = relationship("User", back_populates="reviews")
    AlbumReview.album = relationship("Album", back_populates="reviews")

    # Настраиваем отношения для AlbumRating
    AlbumRating.user = relationship("User", back_populates="ratings")
    AlbumRating.album = relationship("Album", back_populates="ratings")