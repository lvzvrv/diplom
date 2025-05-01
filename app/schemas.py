from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: str
    is_critic: bool = False


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class AlbumBase(BaseModel):
    album_title: str
    artist_name: str
    release_date: datetime
    genre: Optional[str] = None
    cover_url: Optional[str] = None


class AlbumResponse(AlbumBase):
    id: int
    user_score: float
    critic_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    review_text: str
    score: int = Field(..., ge=1, le=100)


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    username: str
    is_critic: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlbumDetailResponse(AlbumResponse):
    reviews: List[ReviewResponse] = []