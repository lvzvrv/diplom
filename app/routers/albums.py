import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer
from ..database import get_db
from ..models.album import Album
from ..models.album_review import AlbumReview
from ..models.user import User
from ..routers.users import get_current_user
from datetime import datetime

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")
csrf_serializer = URLSafeTimedSerializer(os.getenv("CSRF_SECRET_KEY"))

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

    current_user = None
    if request.cookies.get("access_token"):
        try:
            current_user = await get_current_user(request, db)
        except Exception as e:
            print(f"Auth error: {e}")

    csrf_token = csrf_serializer.dumps("csrf_protection")
    request.session["csrf_token"] = csrf_token

    album_data = {
        **album.__dict__,
        "reviews": [{
            "id": review.id,
            "review_text": review.review_text,
            "score": review.score,
            "created_at": review.created_at,
            "user_id": user.id,
            "username": user.username,
            "is_critic_review": review.is_critic_review
        } for review, user in reviews],
        "csrf_token": csrf_token
    }

    return templates.TemplateResponse(
        "album_detail.html",
        {
            "request": request,
            "album": album_data,
            "current_user": current_user  # Добавлено отдельно
        }
    )

@router.post("/albums/{album_id}/reviews")
async def add_review(
    album_id: int,
    request: Request,
    review_text: str = Form(...),
    score: int = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session_token = request.session.get("csrf_token")
    if not session_token or session_token != csrf_token:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    if not 0 <= score <= 100:
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100")

    existing_review = db.query(AlbumReview).filter(
        AlbumReview.album_id == album_id,
        AlbumReview.user_id == current_user.id
    ).first()

    if existing_review:
        raise HTTPException(status_code=400, detail="You've already reviewed this album")

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
    update_album_scores(db, album_id)

    return RedirectResponse(url=f"/albums/{album_id}", status_code=303)

def update_album_scores(db: Session, album_id: int):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        return

    reviews = db.query(AlbumReview).filter(AlbumReview.album_id == album_id).all()

    if reviews:
        total_score = sum(r.score for r in reviews)
        album.user_score = total_score / len(reviews)

        critic_reviews = [r for r in reviews if r.is_critic_review]
        if critic_reviews:
            total_critic_score = sum(r.score for r in critic_reviews)
            album.critic_score = total_critic_score / len(critic_reviews)

    db.commit()