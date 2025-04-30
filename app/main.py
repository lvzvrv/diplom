from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import users, root, albums, admin
from app.utils import STATIC_DIR
from dotenv import load_dotenv
import os

load_dotenv()  # Загружаем переменные

print("DB_USER:", os.getenv('DB_USER'))
print("DB_NAME:", os.getenv('DB_NAME'))
app = FastAPI()


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


app.include_router(users.router, tags=["Users"])
app.include_router(root.router, tags=["Root"])
# app.include_router(albums.router, tags = ["Albums"])
app.include_router(admin.router, tags = ["Admin"])
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
