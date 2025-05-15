from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..models.album import Album
from ..models.album_review import AlbumReview
from ..routers.users import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/profile")
async def profile_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Получаем отзывы пользователя с информацией об альбомах
    reviews = db.query(AlbumReview, Album).join(
        Album, AlbumReview.album_id == Album.id
    ).filter(
        AlbumReview.user_id == current_user.id
    ).order_by(
        AlbumReview.created_at.desc()
    ).all()

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "current_user": current_user,
            "reviews": [{
                "id": review.id,
                "review_text": review.review_text,
                "score": review.score,
                "created_at": review.created_at,
                "is_critic_review": review.is_critic_review,
                "album_id": album.id,
                "album_title": album.album_title,
                "artist_name": album.artist_name,
                "cover_url": album.cover_url
            } for review, album in reviews]
        }
    )