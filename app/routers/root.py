import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.utils import TEMPLATES_DIR

router = APIRouter()  # Обязательно должно быть "router"

templates = Jinja2Templates(directory=TEMPLATES_DIR)

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/top-albums", )
async def top_albums(request: Request):
    return {"Лучшие альбомы": "вот они"}