from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=schemas.Token)
def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Un utilisateur avec cet email existe déjà",
        )
    
    # Créer l'organisation si fournie
    organization = None
    if user_in.organization_name:
        org_in = schemas.OrganizationCreate(
            name=user_in.organization_name,
            plan_type="free"
        )
        organization = crud.organization.create(db, obj_in=org_in)
    
    # Créer l'utilisateur
    user = crud.user.create(db, obj_in=user_in)
    
    # Activer l'utilisateur automatiquement lors de l'inscription
    user.is_verified = True
    db.commit()
    db.refresh(user)
    
    # Associer l'utilisateur à l'organisation
    if organization:
        user.organization_id = organization.id
        user.role = "admin"
        db.commit()
        db.refresh(user)
    
    # Générer les tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.email, expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    
    # Mettre à jour la dernière connexion
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.email, expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(
    *,
    db: Session = Depends(deps.get_db),
    refresh_data: schemas.RefreshTokenRequest,
) -> Any:
    try:
        email = security.verify_token(refresh_data.refresh_token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de rafraîchissement invalide",
            )
        
        user = crud.user.get_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé",
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.email, expires_delta=access_token_expires
        )
        new_refresh_token = security.create_refresh_token(user.email)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de rafraîchissement invalide",
        )


@router.get("/me", response_model=schemas.User)
def read_users_me(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return current_user
