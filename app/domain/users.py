from enum import StrEnum
from pydantic import BaseModel, EmailStr


class UserRole(StrEnum):
    user = "user"
    admin = "admin"


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool