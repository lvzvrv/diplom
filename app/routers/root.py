import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

from app.database import get_db
from app.models.album import Album
from app.routers.users import get_current_user
from app.models.user import User

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def read_albums(
    request: Request,
    db: Session = Depends(get_db)
):
    # Получаем список альбомов
    albums = db.query(Album).order_by(Album.release_date.desc()).all()

    # Проверяем авторизацию через JWT
    current_user = None
    if request.cookies.get("access_token"):
        try:
            current_user = await get_current_user(request, db)
        except:
            # Если токен невалидный, удаляем его
            response = templates.TemplateResponse(
                "index.html",
                {"request": request, "albums": albums, "current_user": None}
            )
            response.delete_cookie("access_token")
            return response

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "albums": albums,
            "current_user": current_user  # Используем единое именование
        }
    )

@router.get("/top-albums", response_class=HTMLResponse)
async def top_albums(
    request: Request,
    db: Session = Depends(get_db)
):
    # Получаем топ альбомов по рейтингу
    top_albums = db.query(Album).order_by(Album.user_score.desc()).limit(10).all()

    # Проверяем авторизацию
    current_user = None
    if request.cookies.get("access_token"):
        try:
            current_user = await get_current_user(request, db)
        except:
            pass

    return templates.TemplateResponse(
        "top_albums.html",  # Создайте этот шаблон
        {
            "request": request,
            "albums": top_albums,
            "current_user": current_user
        }
    )