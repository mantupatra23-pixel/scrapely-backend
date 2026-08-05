import uuid
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
