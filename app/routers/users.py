import os
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models.user import User
from app.utils import get_password_hash, verify_password
from app.utils import TEMPLATES_DIR

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Временное хранилище сессий (в продакшене используйте JWT)
sessions = {}


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        mode = request.query_params.get("mode", "login")
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "mode": mode
        })

    db = SessionLocal()
    user = db.query(User).filter(User.id == sessions[session_id]).first()
    db.close()

    if not user:
        response = RedirectResponse(url="/profile", status_code=303)
        response.delete_cookie("session_id")
        return response

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user  # Передаем полный объект пользователя
    })


@router.post("/login")
async def login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...)
):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()

    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "mode": "login",
            "error": "Неверное имя пользователя или пароль"
        })

    # Создаем сессию (в продакшене используйте JWT)
    session_id = os.urandom(16).hex()
    sessions[session_id] = user.id  # Сохраняем только ID

    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response


@router.post("/register")
async def register(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)
):
    db = SessionLocal()
    try:
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Автоматический вход после регистрации
        session_id = os.urandom(16).hex()
        sessions[session_id] = user.id

        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response

    except IntegrityError as e:
        db.rollback()
        error_msg = "Пользователь с таким именем уже существует" if "username" in str(
            e) else "Пользователь с таким email уже существует"
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "mode": "register",
            "error": error_msg
        })
    finally:
        db.close()


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("session_id")
    return response