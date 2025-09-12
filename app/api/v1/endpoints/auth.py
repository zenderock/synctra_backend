from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
import secrets
import string

from app.core.database import get_db
from app.core.security import (
    authenticate_user, 
    create_access_token, 
    create_refresh_token,
    get_password_hash,
    verify_token
)
from app.core.deps import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import (
    UserRegister, 
    UserLogin, 
    TokenRefresh, 
    TokenResponse, 
    UserProfile
)
from app.core.exceptions import ValidationException, AuthenticationException

router = APIRouter()

def generate_slug(name: str) -> str:
    base_slug = name.lower().replace(" ", "-").replace("'", "")
    base_slug = ''.join(c for c in base_slug if c.isalnum() or c == '-')
    return base_slug[:50]

def generate_api_key() -> str:
    return f"sk_live_{''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))}"

def generate_project_id(name: str) -> str:
    base_id = name.lower().replace(" ", "_").replace("'", "")
    base_id = ''.join(c for c in base_id if c.isalnum() or c == '_')
    return f"{base_id[:20]}_2024"

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise ValidationException("Cet email est déjà utilisé", "email")
    
    org_slug = generate_slug(user_data.organization_name)
    existing_org = db.query(Organization).filter(Organization.slug == org_slug).first()
    if existing_org:
        org_slug = f"{org_slug}-{secrets.token_hex(4)}"
    
    organization = Organization(
        name=user_data.organization_name,
        slug=org_slug,
        plan_type="free"
    )
    db.add(organization)
    db.flush()
    
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        organization_id=organization.id,
        role="admin",
        is_verified=True
    )
    db.add(user)
    db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=900
    )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise AuthenticationException("Email ou mot de passe incorrect")
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=900
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    payload = verify_token(token_data.refresh_token, "refresh")
    user_id = payload.get("sub")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationException("Utilisateur non trouvé")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=900
    )

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        is_verified=current_user.is_verified,
        organization_id=str(current_user.organization_id)
    )
