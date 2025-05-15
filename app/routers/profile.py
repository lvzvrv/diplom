from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..routers.users import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/profile")
async def profile_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "current_user": current_user  # Добавляем current_user в контекст
        }
    )