from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str
    is_critic: bool = False

class UserCreate(UserBase):
    password: str  # Пароль в открытом виде (для регистрации)

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    is_critic: Optional[bool] = None
    is_active: Optional[bool] = None