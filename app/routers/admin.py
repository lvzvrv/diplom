from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import Query as FastAPIQuery
import secrets
import logging
from pathlib import Path

from starlette.responses import RedirectResponse

from app.models import Album, AlbumReview
from app.models.user import User
from app.database import get_db
from app.schemas import UserResponse
from app.utils import TEMPLATES_DIR

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

security = HTTPBasic()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Создаем папку для partials если ее нет
partials_dir = Path(TEMPLATES_DIR) / "partials"
partials_dir.mkdir(exist_ok=True)


def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "admin123")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@router.get("")
async def admin_dashboard(
    request: Request,
    admin: str = Depends(get_current_admin)
):
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "is_htmx": request.headers.get("hx-request") == "true"
        }
    )

@router.get("/users", response_model=list[UserResponse])
async def admin_users_page(
        request: Request,
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    users = db.query(User).order_by(User.id).all()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "users": users,
            "is_htmx": request.headers.get("hx-request") == "true"
        }
    )


@router.patch("/users/{user_id}")
async def update_user_role(
        user_id: int,
        request: Request,
        is_critic: bool = Form(...),
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    try:
        logger.info(f"Updating user {user_id} to is_critic={is_critic}")

        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        db_user.is_critic = is_critic
        db.commit()
        db.refresh(db_user)

        is_htmx = request.headers.get("hx-request") == "true"

        if is_htmx:
            # Возвращаем только строку таблицы для HTMX
            return templates.TemplateResponse(
                "partials/user_row.html",
                {
                    "request": request,
                    "user": db_user
                }
            )
        else:
            # Полная перезагрузка (на случай отключения JS)
            return RedirectResponse(url="/admin/users", status_code=303)

    except Exception as e:
        logger.error(f"Error updating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.api_route("/users/{user_id}", methods=["GET", "POST"])
async def fallback_handler():
    return RedirectResponse(url="/admin/users")


@router.get("/albums")
async def admin_albums_page(
        request: Request,
        search: Optional[str] = FastAPIQuery(None),
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    db_query = db.query(Album).order_by(Album.id)

    if search:
        db_query = db_query.filter(
            or_(
                Album.album_title.ilike(f"%{search}%"),
                Album.artist_name.ilike(f"%{search}%")
            )
        )

    albums = db_query.all()

    # Определяем какой шаблон использовать
    if request.headers.get("hx-request"):
        template_name = "partials/albums_table.html"
    else:
        template_name = "admin_albums.html"

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "albums": albums,
            "search_query": search or ""
        }
    )


@router.get("/albums/new")
async def new_album_form(
        request: Request,
        admin: str = Depends(get_current_admin)
):
    return templates.TemplateResponse(
        "admin_album_form.html",
        {
            "request": request,
            "album": None,
            "action_url": "/admin/albums",
            "form_title": "Добавить новый альбом"
        }
    )


@router.post("/albums")
async def create_album(
        request: Request,
        album_title: str = Form(...),
        artist_name: str = Form(...),
        release_date: str = Form(...),
        genre: str = Form(...),
        cover_url: str = Form(default=None),
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    try:
        release_date_obj = datetime.strptime(release_date, "%Y-%m-%d").date()

        album = Album(
            album_title=album_title,
            artist_name=artist_name,
            release_date=release_date_obj,
            genre=genre,
            cover_url=cover_url,
            user_score=0.0,
            critic_score=0.0,
            created_at=datetime.utcnow()
        )

        db.add(album)
        db.commit()
        db.refresh(album)

        return RedirectResponse(url="/admin/albums", status_code=303)

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating album: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/albums/{album_id}/edit")
async def edit_album_form(
        request: Request,
        album_id: int,
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    return templates.TemplateResponse(
        "admin_album_form.html",
        {
            "request": request,
            "album": album,
            "action_url": f"/admin/albums/{album_id}",
            "form_title": "Редактировать альбом"
        }
    )


@router.post("/albums/{album_id}")
async def update_album(
        request: Request,
        album_id: int,
        album_title: str = Form(...),
        artist_name: str = Form(...),
        release_date: str = Form(...),
        genre: str = Form(...),
        cover_url: str = Form(default=None),
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    try:
        album = db.query(Album).filter(Album.id == album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")

        release_date_obj = datetime.strptime(release_date, "%Y-%m-%d").date()

        album.album_title = album_title
        album.artist_name = artist_name
        album.release_date = release_date_obj
        album.genre = genre
        if cover_url:
            album.cover_url = cover_url

        db.commit()
        db.refresh(album)

        return RedirectResponse(url="/admin/albums", status_code=303)

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating album: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/albums/{album_id}/delete")
async def delete_album(
        request: Request,
        album_id: int,
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    try:
        album = db.query(Album).filter(Album.id == album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")

        db.delete(album)
        db.commit()

        return RedirectResponse(url="/admin/albums", status_code=303)

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting album: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/reviews")
async def admin_reviews_page(
    request: Request,
    search: Optional[str] = FastAPIQuery(None),
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    # Базовый запрос с join таблиц
    query = db.query(AlbumReview, Album, User).join(
        Album, AlbumReview.album_id == Album.id
    ).join(
        User, AlbumReview.user_id == User.id
    ).order_by(AlbumReview.created_at.desc())

    if search:
        query = query.filter(
            or_(
                Album.album_title.ilike(f"%{search}%"),
                Album.artist_name.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                AlbumReview.review_text.ilike(f"%{search}%")
            )
        )

    reviews_data = query.all()

    # Форматируем данные для шаблона
    reviews = []
    for review, album, user in reviews_data:
        reviews.append({
            "id": review.id,
            "album_id": album.id,
            "album_title": album.album_title,
            "artist_name": album.artist_name,
            "username": user.username,
            "is_critic": review.is_critic_review,
            "score": review.score,
            "review_text": review.review_text,
            "created_at": review.created_at
        })

    if request.headers.get("hx-request"):
        template_name = "partials/reviews_table.html"
    else:
        template_name = "admin_reviews.html"

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "reviews": reviews,
            "search_query": search or ""
        }
    )

def update_user_score(db: Session, album_id: int):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        return

    reviews = db.query(AlbumReview).filter(
        AlbumReview.album_id == album_id,
        AlbumReview.is_critic_review == False
    ).all()

    if reviews:
        total_score = sum(r.score for r in reviews)
        album.user_score = total_score / len(reviews)
    else:
        album.user_score = 0.0

    db.commit()

def update_critic_score(db: Session, album_id: int):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        return

    reviews = db.query(AlbumReview).filter(
        AlbumReview.album_id == album_id,
        AlbumReview.is_critic_review == True
    ).all()

    if reviews:
        total_score = sum(r.score for r in reviews)
        album.critic_score = total_score / len(reviews)
    else:
        album.critic_score = 0.0

    db.commit()

@router.post("/reviews/{review_id}/delete")
async def delete_review(
        request: Request,
        review_id: int,
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    try:
        review = db.query(AlbumReview).filter(AlbumReview.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        album_id = review.album_id
        is_critic_review = review.is_critic_review

        db.delete(review)
        db.commit()

        # Обновляем соответствующий рейтинг альбома
        if is_critic_review:
            update_critic_score(db, album_id)
        else:
            update_user_score(db, album_id)

        if request.headers.get("hx-request"):
            return ""
        return RedirectResponse(url="/admin/reviews", status_code=303)

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting review: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=str(e))