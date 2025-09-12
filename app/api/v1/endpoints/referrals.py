from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import secrets
import string

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_project_by_id
from app.models.user import User
from app.models.project import Project
from app.models.referral_code import ReferralCode
from app.schemas.referral import ReferralCodeCreate, ReferralCodeUpdate, ReferralCodeResponse, ReferralUse
from app.core.exceptions import ValidationException, NotFoundException

router = APIRouter()

@router.get("/", response_model=List[ReferralCodeResponse])
async def get_referral_codes(
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    codes = db.query(ReferralCode).filter(
        ReferralCode.project_id == project.id
    ).all()
    return codes

@router.post("/", response_model=ReferralCodeResponse)
async def create_referral_code(
    code_data: ReferralCodeCreate,
    project: Project = Depends(get_project_by_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    existing_code = db.query(ReferralCode).filter(
        ReferralCode.code == code_data.code
    ).first()
    
    if existing_code:
        raise ValidationException("Ce code de parrainage existe déjà", "code")
    
    referral_code = ReferralCode(
        project_id=project.id,
        code=code_data.code,
        user_id=current_user.id,
        reward_type=code_data.reward_type,
        reward_value=code_data.reward_value,
        max_uses=code_data.max_uses,
        expires_at=code_data.expires_at
    )
    
    db.add(referral_code)
    db.commit()
    db.refresh(referral_code)
    
    return referral_code

@router.get("/{code_id}", response_model=ReferralCodeResponse)
async def get_referral_code(
    code_id: str,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    code = db.query(ReferralCode).filter(
        ReferralCode.id == code_id,
        ReferralCode.project_id == project.id
    ).first()
    
    if not code:
        raise NotFoundException("Code de parrainage non trouvé")
    
    return code

@router.put("/{code_id}", response_model=ReferralCodeResponse)
async def update_referral_code(
    code_id: str,
    code_data: ReferralCodeUpdate,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    code = db.query(ReferralCode).filter(
        ReferralCode.id == code_id,
        ReferralCode.project_id == project.id
    ).first()
    
    if not code:
        raise NotFoundException("Code de parrainage non trouvé")
    
    update_data = code_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(code, field, value)
    
    db.commit()
    db.refresh(code)
    
    return code

@router.post("/validate")
async def validate_referral_code(
    use_data: ReferralUse,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    code = db.query(ReferralCode).filter(
        ReferralCode.code == use_data.code,
        ReferralCode.project_id == project.id,
        ReferralCode.is_active == True
    ).first()
    
    if not code:
        return {"valid": False, "message": "Code de parrainage invalide"}
    
    if code.expires_at and code.expires_at < datetime.utcnow():
        return {"valid": False, "message": "Code de parrainage expiré"}
    
    if code.max_uses and code.current_uses >= code.max_uses:
        return {"valid": False, "message": "Code de parrainage épuisé"}
    
    return {
        "valid": True,
        "reward_type": code.reward_type,
        "reward_value": code.reward_value,
        "message": "Code de parrainage valide"
    }

@router.post("/use")
async def use_referral_code(
    use_data: ReferralUse,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    code = db.query(ReferralCode).filter(
        ReferralCode.code == use_data.code,
        ReferralCode.project_id == project.id,
        ReferralCode.is_active == True
    ).first()
    
    if not code:
        raise ValidationException("Code de parrainage invalide")
    
    if code.expires_at and code.expires_at < datetime.utcnow():
        raise ValidationException("Code de parrainage expiré")
    
    if code.max_uses and code.current_uses >= code.max_uses:
        raise ValidationException("Code de parrainage épuisé")
    
    code.current_uses += 1
    db.commit()
    
    return {
        "success": True,
        "reward_type": code.reward_type,
        "reward_value": code.reward_value,
        "message": "Code de parrainage utilisé avec succès"
    }

@router.delete("/{code_id}")
async def delete_referral_code(
    code_id: str,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    code = db.query(ReferralCode).filter(
        ReferralCode.id == code_id,
        ReferralCode.project_id == project.id
    ).first()
    
    if not code:
        raise NotFoundException("Code de parrainage non trouvé")
    
    db.delete(code)
    db.commit()
    
    return {"message": "Code de parrainage supprimé avec succès"}
