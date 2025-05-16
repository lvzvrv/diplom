import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, Query
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


@router.get("/new-releases", response_class=HTMLResponse)
async def new_releases(
        request: Request,
        page: int = Query(1, ge=1, description="Номер страницы"),
        per_page: int = Query(10, ge=5, le=50, description="Количество альбомов на странице"),
        min_user_score: int = Query(0, ge=0, le=100, description="Минимальный пользовательский рейтинг"),
        min_critic_score: int = Query(0, ge=0, le=100, description="Минимальный рейтинг критиков"),
        db: Session = Depends(get_db)
):
    """
    Отображает страницу с новыми релизами (альбомами, выпущенными за последние 30 дней)
    с поддержкой пагинации и фильтрации по рейтингу.
    """
    # Вычисляем дату 30 дней назад от текущей даты
    thirty_days_ago = datetime.now() - timedelta(days=30)

    # Базовый запрос с фильтрацией по дате
    query = db.query(Album).filter(
        Album.release_date >= thirty_days_ago
    )

    # Применяем фильтрацию по рейтингу, если указаны минимальные значения
    if min_user_score > 0:
        query = query.filter(Album.user_score >= min_user_score)

    if min_critic_score > 0:
        query = query.filter(Album.critic_score >= min_critic_score)

    # Получаем общее количество альбомов (для пагинации)
    total_albums = query.count()

    # Применяем пагинацию и сортировку по дате выхода (новые сначала)
    albums = query.order_by(
        Album.release_date.desc()
    ).offset(
        (page - 1) * per_page
    ).limit(
        per_page
    ).all()

    # Проверка авторизации пользователя
    current_user = None
    if request.cookies.get("access_token"):
        try:
            current_user = await get_current_user(request, db)
        except:
            # Если токен невалидный, удаляем его и показываем страницу как для неавторизованного пользователя
            response = templates.TemplateResponse(
                "new_releases.html",
                {
                    "request": request,
                    "albums": albums,
                    "current_user": None,
                    "page": page,
                    "per_page": per_page,
                    "total_albums": total_albums,
                    "min_user_score": min_user_score,
                    "min_critic_score": min_critic_score
                }
            )
            response.delete_cookie("access_token")
            return response

    return templates.TemplateResponse(
        "new_releases.html",
        {
            "request": request,
            "albums": albums,
            "current_user": current_user,
            "page": page,
            "per_page": per_page,
            "total_albums": total_albums,
            "min_user_score": min_user_score,
            "min_critic_score": min_critic_score,
            "total_pages": (total_albums + per_page - 1) // per_page  # Округляем вверх
        }
    )