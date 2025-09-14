from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import secrets
import string

from app.core.database import get_db
from app.core.sdk_auth import get_api_key_auth
from app.models.project import Project
from app.models.referral_code import ReferralCode
from app.schemas.sdk import (
    ReferralCodeCreate,
    ReferralCodeUpdate, 
    ReferralCodeResponse,
    ReferralCodeUse,
    SDKResponse,
    ReferralAnalyticsResponse
)

router = APIRouter()

def generate_referral_code() -> str:
    """Générer un code de parrainage unique."""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

@router.post("/", status_code=201)
async def create_referral_code(
    referral_data: ReferralCodeCreate,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Créer un nouveau code de parrainage."""
    
    # Générer un code si non fourni
    code = referral_data.code or generate_referral_code()
    
    # Vérifier l'unicité du code dans le projet
    existing = db.query(ReferralCode).filter(
        ReferralCode.project_id == project.id,
        ReferralCode.code == code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Ce code de parrainage existe déjà",
                "code": "REFERRAL_CODE_EXISTS"
            }
        )
    
    referral = ReferralCode(
        project_id=project.id,
        code=code,
        user_id=referral_data.userId,
        expires_at=referral_data.expiresAt,
        max_uses=referral_data.maxUses,
        reward_amount=referral_data.rewardAmount,
        reward_type=referral_data.rewardType,
        metadata=referral_data.metadata
    )
    
    db.add(referral)
    db.commit()
    db.refresh(referral)
    
    return SDKResponse(
        success=True,
        data=ReferralCodeResponse(
            code=referral.code,
            userId=referral.user_id,
            campaignId=referral_data.campaignId,
            createdAt=referral.created_at,
            expiresAt=referral.expires_at,
            maxUses=referral.max_uses,
            currentUses=referral.current_uses,
            isActive=referral.is_active,
            metadata=referral.metadata,
            rewardAmount=referral.reward_amount,
            rewardType=referral.reward_type
        )
    )

@router.get("/{code}")
async def get_referral_code(
    code: str,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Récupérer un code de parrainage."""
    
    referral = db.query(ReferralCode).filter(
        ReferralCode.project_id == project.id,
        ReferralCode.code == code
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Code de parrainage non trouvé",
                "code": "REFERRAL_NOT_FOUND"
            }
        )
    
    return SDKResponse(
        success=True,
        data=ReferralCodeResponse(
            code=referral.code,
            userId=referral.user_id,
            campaignId=None,  # TODO: ajouter campaign_id au modèle
            createdAt=referral.created_at,
            expiresAt=referral.expires_at,
            maxUses=referral.max_uses,
            currentUses=referral.current_uses,
            isActive=referral.is_active,
            metadata=referral.metadata,
            rewardAmount=referral.reward_amount,
            rewardType=referral.reward_type
        )
    )

@router.get("/")
async def list_referral_codes(
    userId: str = Query(..., description="ID de l'utilisateur"),
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Lister les codes de parrainage d'un utilisateur."""
    
    referrals = db.query(ReferralCode).filter(
        ReferralCode.project_id == project.id,
        ReferralCode.user_id == userId
    ).all()
    
    referral_responses = []
    for referral in referrals:
        referral_responses.append(ReferralCodeResponse(
            code=referral.code,
            userId=referral.user_id,
            campaignId=None,
            createdAt=referral.created_at,
            expiresAt=referral.expires_at,
            maxUses=referral.max_uses,
            currentUses=referral.current_uses,
            isActive=referral.is_active,
            metadata=referral.metadata,
            rewardAmount=referral.reward_amount,
            rewardType=referral.reward_type
        ))
    
    return SDKResponse(
        success=True,
        data={"referrals": referral_responses}
    )

@router.post("/{code}/use")
async def use_referral_code(
    code: str,
    use_data: ReferralCodeUse,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Utiliser un code de parrainage."""
    
    referral = db.query(ReferralCode).filter(
        ReferralCode.project_id == project.id,
        ReferralCode.code == code,
        ReferralCode.is_active == True
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Code de parrainage non trouvé ou inactif",
                "code": "REFERRAL_NOT_FOUND"
            }
        )
    
    # Vérifier si le code n'est pas expiré
    if referral.expires_at and referral.expires_at < use_data.timestamp:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Code de parrainage expiré",
                "code": "REFERRAL_EXPIRED"
            }
        )
    
    # Vérifier les limites d'utilisation
    if referral.current_uses >= referral.max_uses:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Limite d'utilisation du code atteinte",
                "code": "REFERRAL_LIMIT_REACHED"
            }
        )
    
    # Incrémenter l'utilisation
    referral.current_uses += 1
    db.commit()
    db.refresh(referral)
    
    return SDKResponse(
        success=True,
        data=ReferralCodeResponse(
            code=referral.code,
            userId=referral.user_id,
            campaignId=None,
            createdAt=referral.created_at,
            expiresAt=referral.expires_at,
            maxUses=referral.max_uses,
            currentUses=referral.current_uses,
            isActive=referral.is_active,
            metadata=referral.metadata,
            rewardAmount=referral.reward_amount,
            rewardType=referral.reward_type
        )
    )

@router.put("/{code}")
async def update_referral_code(
    code: str,
    referral_data: ReferralCodeUpdate,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Mettre à jour un code de parrainage."""
    
    referral = db.query(ReferralCode).filter(
        ReferralCode.project_id == project.id,
        ReferralCode.code == code
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Code de parrainage non trouvé",
                "code": "REFERRAL_NOT_FOUND"
            }
        )
    
    update_data = referral_data.dict(exclude_unset=True)
    
    # Mapper les champs
    field_mapping = {
        'expiresAt': 'expires_at',
        'maxUses': 'max_uses',
        'isActive': 'is_active',
        'rewardAmount': 'reward_amount',
        'rewardType': 'reward_type'
    }
    
    for sdk_field, db_field in field_mapping.items():
        if sdk_field in update_data:
            setattr(referral, db_field, update_data[sdk_field])
    
    if 'metadata' in update_data:
        referral.metadata = update_data['metadata']
    
    db.commit()
    db.refresh(referral)
    
    return SDKResponse(
        success=True,
        data=ReferralCodeResponse(
            code=referral.code,
            userId=referral.user_id,
            campaignId=None,
            createdAt=referral.created_at,
            expiresAt=referral.expires_at,
            maxUses=referral.max_uses,
            currentUses=referral.current_uses,
            isActive=referral.is_active,
            metadata=referral.metadata,
            rewardAmount=referral.reward_amount,
            rewardType=referral.reward_type
        )
    )

@router.delete("/{code}", status_code=204)
async def delete_referral_code(
    code: str,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Supprimer un code de parrainage."""
    
    referral = db.query(ReferralCode).filter(
        ReferralCode.project_id == project.id,
        ReferralCode.code == code
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Code de parrainage non trouvé",
                "code": "REFERRAL_NOT_FOUND"
            }
        )
    
    db.delete(referral)
    db.commit()

@router.get("/{code}/analytics")
async def get_referral_analytics(
    code: str,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Analytics d'un code de parrainage."""
    
    referral = db.query(ReferralCode).filter(
        ReferralCode.project_id == project.id,
        ReferralCode.code == code
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Code de parrainage non trouvé",
                "code": "REFERRAL_NOT_FOUND"
            }
        )
    
    # TODO: Implémenter la logique d'analytics réelle
    return SDKResponse(
        success=True,
        data=ReferralAnalyticsResponse(
            totalUses=referral.current_uses,
            uniqueUsers=0,  # TODO: calculer les utilisateurs uniques
            conversions=0,  # TODO: calculer les conversions
            revenue=0.0,    # TODO: calculer le revenu
            timeline=[]     # TODO: données temporelles
        )
    )
