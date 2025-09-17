from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "member"


class UserCreate(UserBase):
    password: str
    organization_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None


class UserInDBBase(UserBase):
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    password_hash: str


class UserCreateFromInvitation(BaseModel):
    first_name: str
    last_name: str
    password: str
