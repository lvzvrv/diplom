from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import secrets
import logging
from pathlib import Path

from starlette.responses import RedirectResponse

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