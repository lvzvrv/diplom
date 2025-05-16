from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func

from app.database import get_db
from app.models.album import Album
from app.routers.users import get_current_user
from urllib.parse import unquote

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/genres", response_class=HTMLResponse)
async def show_genres(
        request: Request,
        db: Session = Depends(get_db)
):
    # Получаем уникальные жанры из базы данных
    genres = db.query(func.lower(Album.genre)).distinct().filter(Album.genre != None).all()
    genres = [genre[0].capitalize() for genre in genres if genre[0]]  # Приводим к нормальному виду

    # Проверка авторизации
    current_user = None
    if request.cookies.get("access_token"):
        try:
            current_user = await get_current_user(request, db)
        except:
            response = templates.TemplateResponse(
                "genres.html",
                {"request": request, "genres": genres, "current_user": None}
            )
            response.delete_cookie("access_token")
            return response

    return templates.TemplateResponse(
        "genres.html",
        {"request": request, "genres": genres, "current_user": current_user}
    )


@router.get("/genres/{genre_name:path}", response_class=HTMLResponse)  # Обратите внимание на :path
async def show_albums_by_genre(
        request: Request,
        genre_name: str,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=5, le=50),
        db: Session = Depends(get_db)
):
    # Декодируем URL-encoded строку (например, заменяем %20 на пробелы)
    decoded_genre = unquote(genre_name)

    # Получаем альбомы по жанру (без учета регистра)
    query = db.query(Album).filter(func.lower(Album.genre) == func.lower(decoded_genre))

    total_albums = query.count()
    albums = query.order_by(Album.release_date.desc()
                            ).offset((page - 1) * per_page
                                     ).limit(per_page).all()

    # Проверка авторизации
    current_user = None
    if request.cookies.get("access_token"):
        try:
            current_user = await get_current_user(request, db)
        except:
            response = templates.TemplateResponse(
                "genre_albums.html",
                {
                    "request": request,
                    "albums": albums,
                    "genre": decoded_genre.capitalize(),
                    "current_user": None,
                    "page": page,
                    "per_page": per_page,
                    "total_albums": total_albums
                }
            )
            response.delete_cookie("access_token")
            return response

    return templates.TemplateResponse(
        "genre_albums.html",
        {
            "request": request,
            "albums": albums,
            "genre": decoded_genre.capitalize(),
            "current_user": current_user,
            "page": page,
            "per_page": per_page,
            "total_albums": total_albums,
            "total_pages": (total_albums + per_page - 1) // per_page
        }
    )