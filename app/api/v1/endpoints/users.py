from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    # Vérifier que l'utilisateur a une organisation
    if not current_user.organization_id:
        raise HTTPException(status_code=403, detail="Vous devez faire partie d'une organisation")
    
    # Récupérer les utilisateurs de la même organisation
    users = crud.user.get_by_organization(db, organization_id=current_user.organization_id)
    return users


@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user
