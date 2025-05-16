from datetime import datetime
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.database import get_db
from app.models.album import Album
from app.routers.users import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_update_query_param(request: Request):
    def update_query_param(param: str, value: any):
        params = dict(request.query_params)
        params[param] = value
        return str(request.url.include_query_params(**params))

    return update_query_param


@router.get("/all-releases", response_class=HTMLResponse)
async def all_releases(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(12, ge=5, le=50),
        min_user_score: int = Query(0, ge=0, le=100),
        min_critic_score: int = Query(0, ge=0, le=100),
        year_from: int = Query(1900, ge=1900, le=datetime.now().year),
        year_to: int = Query(datetime.now().year, ge=1900, le=datetime.now().year),
        sort_by: str = Query("date_desc", description="Сортировка: date_desc, date_asc, user_rating, critic_rating"),
        db: Session = Depends(get_db)
):
    current_year = datetime.now().year
    update_query_param = get_update_query_param(request)

    # Базовый запрос
    query = db.query(Album)

    # Применяем фильтры
    if min_user_score > 0:
        query = query.filter(Album.user_score >= min_user_score)
    if min_critic_score > 0:
        query = query.filter(Album.critic_score >= min_critic_score)
    if year_from or year_to:
        query = query.filter(
            and_(
                Album.release_date >= f"{year_from}-01-01",
                Album.release_date <= f"{year_to}-12-31"
            )
        )

    # Применяем сортировку
    if sort_by == "date_asc":
        query = query.order_by(Album.release_date.asc())
    elif sort_by == "user_rating":
        query = query.order_by(Album.user_score.desc())
    elif sort_by == "critic_rating":
        query = query.order_by(Album.critic_score.desc())
    else:  # date_desc по умолчанию
        query = query.order_by(Album.release_date.desc())

    # Пагинация
    total_albums = query.count()
    albums = query.offset((page - 1) * per_page).limit(per_page).all()

    # Вычисляем диапазон для отображения
    start_item = ((page - 1) * per_page) + 1
    end_item = min(page * per_page, total_albums)

    # Проверка авторизации
    current_user = None
    if request.cookies.get("access_token"):
        try:
            current_user = await get_current_user(request, db)
        except:
            response = templates.TemplateResponse(
                "all_releases.html",
                {
                    "request": request,
                    "albums": albums,
                    "current_user": None,
                    "page": page,
                    "per_page": per_page,
                    "total_albums": total_albums,
                    "total_pages": (total_albums + per_page - 1) // per_page,
                    "current_year": current_year,
                    "start_item": start_item,
                    "end_item": end_item,
                    "filters": {
                        "min_user_score": min_user_score,
                        "min_critic_score": min_critic_score,
                        "year_from": year_from,
                        "year_to": year_to,
                        "sort_by": sort_by
                    },
                    "update_query_param": update_query_param,
                    "min": min,
                    "max": max
                }
            )
            response.delete_cookie("access_token")
            return response

    return templates.TemplateResponse(
        "all_releases.html",
        {
            "request": request,
            "albums": albums,
            "current_user": current_user,
            "page": page,
            "per_page": per_page,
            "total_albums": total_albums,
            "total_pages": (total_albums + per_page - 1) // per_page,
            "current_year": current_year,
            "start_item": start_item,
            "end_item": end_item,
            "filters": {
                "min_user_score": min_user_score,
                "min_critic_score": min_critic_score,
                "year_from": year_from,
                "year_to": year_to,
                "sort_by": sort_by
            },
            "update_query_param": update_query_param,
            "min": min,
            "max": max
        }
    )