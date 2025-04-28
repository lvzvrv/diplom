from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])  # Обязательно должно быть "router"

@router.get("/")
def get_users():
    return {"message": "All users"}

@router.post("/")
def create_user():
    return {"message": "User created"}