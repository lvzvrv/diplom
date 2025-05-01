from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from ..models.album import Album
from ..models.album_review import AlbumReview
from ..models.user import User
from ..database import get_db
from ..schemas import AlbumDetailResponse, ReviewCreate
from fastapi.templating import Jinja2Templates
from ..utils import TEMPLATES_DIR
from datetime import datetime
from ..routers.users import get_current_user
from app.utils import TEMPLATES_DIR

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/albums/{album_id}")
async def get_album(
        album_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    reviews = db.query(AlbumReview, User).join(
        User, AlbumReview.user_id == User.id
    ).filter(
        AlbumReview.album_id == album_id
    ).order_by(
        AlbumReview.created_at.desc()
    ).all()

    album_data = {
        **album.__dict__,
        "reviews": [{
            "id": review.id,
            "review_text": review.review_text,
            "score": review.score,
            "created_at": review.created_at,
            "user_id": user.id,
            "username": user.username,
            "is_critic": user.is_critic
        } for review, user in reviews]
    }

    return templates.TemplateResponse(
        "album_detail.html",
        {"request": request, "album": album_data}
    )


@router.post("/albums/{album_id}/reviews")
async def add_review(
    album_id: int,
    request: Request,
    review_text: str = Form(...),
    score: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Используем нашу функцию
):
    if not 1 <= score <= 100:
        raise HTTPException(status_code=400, detail="Score must be between 1 and 100")

    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    review = AlbumReview(
        album_id=album_id,
        user_id=current_user.id,
        review_text=review_text,
        score=score,
        is_critic_review=current_user.is_critic,
        created_at=datetime.utcnow()
    )

    db.add(review)
    db.commit()

    # Обновляем средние оценки
    update_album_scores(db, album_id)

    return RedirectResponse(
        url=f"/albums/{album_id}",
        status_code=303
    )


def update_album_scores(db: Session, album_id: int):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        return

    reviews = db.query(AlbumReview).filter(
        AlbumReview.album_id == album_id
    ).all()

    if reviews:
        total_score = sum(r.score for r in reviews)
        album.user_score = total_score / len(reviews)

        critic_reviews = [r for r in reviews if r.is_critic_review]
        if critic_reviews:
            total_critic_score = sum(r.score for r in critic_reviews)
            album.critic_score = total_critic_score / len(critic_reviews)

    db.commit()