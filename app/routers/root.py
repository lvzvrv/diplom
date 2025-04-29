import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.database import SessionLocal, Album
from app.models.user import User
from app.routers.users import sessions
from app.utils import TEMPLATES_DIR

router = APIRouter()  # Обязательно должно быть "router"

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", response_class=HTMLResponse)
async def read_albums(request: Request):
    db = SessionLocal()
    albums = db.query(Album).order_by(Album.release_date.desc()).all()

    # Проверяем авторизацию
    session_id = request.cookies.get("session_id")
    user = None
    if session_id and session_id in sessions:
        user = db.query(User).filter(User.id == sessions[session_id]).first()

    db.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "albums": albums,
        "user": user  # Передаем пользователя в шаблон
    })

@router.get("/top-albums", )
async def top_albums(request: Request):
    return {"Лучшие альбомы": "вот они"}