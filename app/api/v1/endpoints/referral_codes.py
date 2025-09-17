from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.schemas.referral_code import ReferralCode, ReferralCodeCreate, ReferralCodeUpdate
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get("/projects/{project_id}/referrals", response_model=List[ReferralCode])
def read_project_referral_codes(
    project_id: str,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve referral codes for a project.
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    
    if not crud.project.can_access(db, project=project, user_id=current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    referral_codes = crud.referral_code.get_by_project(
        db=db, project_id=project_id, skip=skip, limit=limit
    )
    return referral_codes


@router.post("/projects/{project_id}/referrals", response_model=ReferralCode)
def create_referral_code(
    project_id: str,
    referral_in: ReferralCodeCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new referral code.
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    
    if not crud.project.can_access(db, project=project, user_id=current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    # Check if code already exists
    existing_code = crud.referral_code.get_by_code(db=db, code=referral_in.code)
    if existing_code:
        raise HTTPException(
            status_code=400,
            detail="Referral code already exists"
        )
    
    # Set project_id and user_id
    referral_in.project_id = project_id
    referral_in.user_id = current_user.id
    
    referral_code = crud.referral_code.create(db=db, obj_in=referral_in)
    return referral_code


@router.get("/projects/{project_id}/referrals/{referral_id}", response_model=ReferralCode)
def read_referral_code(
    project_id: str,
    referral_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get referral code by ID.
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    
    if not crud.project.can_access(db, project=project, user_id=current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    referral_code = crud.referral_code.get(db=db, id=referral_id)
    if not referral_code or referral_code.project_id != project_id:
        raise HTTPException(
            status_code=404,
            detail="Referral code not found"
        )
    
    return referral_code


@router.put("/projects/{project_id}/referrals/{referral_id}", response_model=ReferralCode)
def update_referral_code(
    project_id: str,
    referral_id: str,
    referral_in: ReferralCodeUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update referral code.
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    
    if not crud.project.can_access(db, project=project, user_id=current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    referral_code = crud.referral_code.get(db=db, id=referral_id)
    if not referral_code or referral_code.project_id != project_id:
        raise HTTPException(
            status_code=404,
            detail="Referral code not found"
        )
    
    referral_code = crud.referral_code.update(db=db, db_obj=referral_code, obj_in=referral_in)
    return referral_code


@router.delete("/projects/{project_id}/referrals/{referral_id}")
def delete_referral_code(
    project_id: str,
    referral_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete referral code.
    """
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    
    if not crud.project.can_access(db, project=project, user_id=current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    referral_code = crud.referral_code.get(db=db, id=referral_id)
    if not referral_code or referral_code.project_id != project_id:
        raise HTTPException(
            status_code=404,
            detail="Referral code not found"
        )
    
    referral_code = crud.referral_code.remove(db=db, id=referral_id)
    return {"message": "Referral code deleted successfully"}
