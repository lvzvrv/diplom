from fastapi import APIRouter

router = APIRouter()  # Обязательно должно быть "router"

@router.get("/{peremennaya}")
def get_users(peremennaya):
    return {"message": f"All users {peremennaya}"}

@router.post("/")
def create_user():
    return {"message": "User created"}