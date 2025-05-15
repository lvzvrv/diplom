import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from jose import jwt, JWTError  # Изменено с import jwt

from ..models.user import User
from ..database import get_db
from ..utils import get_password_hash, verify_password, TEMPLATES_DIR

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Для совместимости (можно удалить если не используется)
sessions = {}

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception

    try:
        if token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth.html", {
        "request": request,
        "mode": "login"
    })


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth.html", {
        "request": request,
        "mode": "register"
    })


@router.post("/login")
async def login_process(
        request: Request,
        response: Response,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "mode": "login",
            "error": "Invalid username or password"
        })

    access_token = create_access_token(data={"sub": user.username})

    # Получаем URL для перенаправления
    redirect_url = request.query_params.get("next", "/")

    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False
    )
    return response


@router.post("/register")
async def register(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    try:
        user = User(
            username=username,
            email=email,
            password=get_password_hash(password),
            is_critic=False,
            is_active=True
        )
        db.add(user)
        db.commit()

        access_token = create_access_token(data={"sub": user.username})

        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False
        )
        return response

    except IntegrityError as e:
        db.rollback()
        error_msg = "Username already exists" if "username" in str(e) else "Email already exists"
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "mode": "register",
            "error": error_msg
        })


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response