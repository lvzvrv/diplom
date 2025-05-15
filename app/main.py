from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer
from pydantic_settings import BaseSettings
from starlette.middleware.sessions import SessionMiddleware

from app.routers import users, root, albums, admin, profile
from app.database import engine
from app.models import Base  # Импортируем Base из models
from app.utils import STATIC_DIR
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles


load_dotenv()

print("DB_USER:", os.getenv('DB_USER'))
print("DB_NAME:", os.getenv('DB_NAME'))

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# Настройки сессии
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY"),
    session_cookie="session",
    max_age=3600
)

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация сериализатора для CSRF
csrf_serializer = URLSafeTimedSerializer(os.getenv("CSRF_SECRET_KEY"))





# Создаем таблицы
Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(users.router, tags=["Users"])
app.include_router(root.router, tags=["Root"])
app.include_router(albums.router, tags=["Albums"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(profile.router, tags=["Profile"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)