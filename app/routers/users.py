from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os

from app.models.user import User
from app.database import get_db
from app.utils import get_password_hash, verify_password, TEMPLATES_DIR
from app.schemas import UserResponse

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

sessions = {}

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    db: Session = Depends(get_db)
):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        mode = request.query_params.get("mode", "login")
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "mode": mode
        })

    user = db.query(User).filter(User.id == sessions[session_id]).first()
    if not user:
        response = RedirectResponse(url="/profile", status_code=303)
        response.delete_cookie("session_id")
        return response

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user
    })

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):  # Используем поле password
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "mode": "login",
            "error": "Invalid username or password"
        })

    session_id = os.urandom(16).hex()
    sessions[session_id] = user.id

    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
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
            password=get_password_hash(password),  # Хешируем пароль, но сохраняем в поле password
            is_critic=False,
            is_active=True
        )
        db.add(user)
        db.commit()

        session_id = os.urandom(16).hex()
        sessions[session_id] = user.id

        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
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
    response.delete_cookie("session_id")
    return response