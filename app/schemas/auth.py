from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr = Field(..., description="Adresse email valide")
    password: str = Field(..., min_length=8, description="Mot de passe (minimum 8 caractères)")
    first_name: str = Field(..., min_length=1, max_length=100, description="Prénom")
    last_name: str = Field(..., min_length=1, max_length=100, description="Nom de famille")
    organization_name: str = Field(..., min_length=1, max_length=255, description="Nom de l'organisation")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Adresse email")
    password: str = Field(..., description="Mot de passe")

class TokenRefresh(BaseModel):
    refresh_token: str = Field(..., description="Token de rafraîchissement")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    organization_name: str
    plan_type: str

class UserProfile(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]
    role: str
    is_verified: bool
    organization_id: str
    
    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
