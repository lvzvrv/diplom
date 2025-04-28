from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import users, root
from app.utils import STATIC_DIR

app = FastAPI()


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(root.router, tags=["Root"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
