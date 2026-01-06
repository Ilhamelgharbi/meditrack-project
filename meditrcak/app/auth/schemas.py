from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.auth.models import RoleEnum

# User Registration Schema
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    role: Optional[RoleEnum] = RoleEnum.patient

# User Response Schema
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    role: RoleEnum
    date_created: datetime

    class Config:
        from_attributes = True

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Token Data Schema
class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
