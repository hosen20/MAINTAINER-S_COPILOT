from pydantic import BaseModel, EmailStr, Field

from app.domain.users import UserRead, UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class AuthenticatedUser(UserRead):
    pass


class UserAuthRecord(BaseModel):
    id: int
    email: EmailStr
    hashed_password: str
    role: UserRole
    is_active: bool