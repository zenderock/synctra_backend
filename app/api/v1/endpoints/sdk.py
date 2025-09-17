from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import crud
from app.api import deps
from app.models.link_click import LinkClick
from app.models.dynamic_link import DynamicLink
from app.models.referral_code import ReferralCode
from app.models.project import Project

router = APIRouter()


async def validate_project_access(
    project_id: str,
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(deps.get_db)
):
    project = db.query(Project).filter(
        Project.api_key == api_key,
        Project.id == project_id
    ).first()
    
    if not project:
        project_exists = db.query(Project).filter(Project.id == project_id).first()
        if project_exists:
            raise HTTPException(status_code=401, detail="API key invalide")
        else:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return project


class DeviceSignatureRequest(BaseModel):
    device_signature: str
    project_id: str
    platform: str


class SignatureMatchResponse(BaseModel):
    found: bool
    link_id: Optional[str] = None
    referral_code: Optional[str] = None


class ConversionTrackingRequest(BaseModel):
    link_id: str
    device_signature: str
    project_id: str
    conversion_value: Optional[float] = None


@router.post("/sdk/match-signature", response_model=SignatureMatchResponse)
async def match_device_signature(
    *,
    signature_request: DeviceSignatureRequest,
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Recherche une signature de device dans les enregistrements d'app non installée
    """
    try:
        # Valider l'accès au projet
        project = await validate_project_access(signature_request.project_id, api_key, db)
        
        # Chercher dans les LinkClick avec browser="app_detection"
        click_records = db.query(LinkClick).filter(
            LinkClick.browser == "app_detection",
            LinkClick.platform == signature_request.platform
        ).all()
        
        # Pour chaque enregistrement, générer une signature et comparer
        for click in click_records:
            # Récupérer le lien associé
            link = crud.dynamic_link.get(db, id=click.link_id)
            if link and str(link.project_id) == str(project.id):
                # Vérifier si le lien est lié à un code de parrainage
                referral_code = None
                if link.link_type == "referral":
                    # Chercher le code de parrainage avec le même short_code
                    referral = db.query(ReferralCode).filter(
                        ReferralCode.code == link.short_code,
                        ReferralCode.project_id == project.id
                    ).first()
                    if referral:
                        referral_code = referral.code
                
                return SignatureMatchResponse(
                    found=True,
                    link_id=str(link.id),
                    referral_code=referral_code
                )
        
        return SignatureMatchResponse(found=False)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sdk/track-conversion")
async def track_conversion(
    *,
    conversion_data: ConversionTrackingRequest,
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Enregistre une conversion (ouverture app via lien)
    """
    try:
        project = await validate_project_access(conversion_data.project_id, api_key, db)
        
        link = db.query(DynamicLink).filter(
            DynamicLink.id == conversion_data.link_id,
            DynamicLink.project_id == project.id
        ).first()
        
        if not link:
            raise HTTPException(status_code=404, detail="Lien non trouvé")
        
        conversion = Conversion(
            id=str(uuid4()),
            link_id=link.id,
            device_signature=conversion_data.device_signature,
            conversion_value=conversion_data.conversion_value,
            project_id=project.id,
            created_at=datetime.utcnow()
        )
        
        db.add(conversion)
        db.commit()
        db.refresh(conversion)
        
        return {
            "success": True,
            "conversion_id": conversion.id,
            "message": "Conversion enregistrée avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sdk/link/{link_short_code}")
async def get_link_data(
    *,
    link_short_code: str,
    project_id: str,
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Récupère les données d'un lien pour le SDK via son short_code
    """
    try:
        project = await validate_project_access(project_id, api_key, db)
        
        link = db.query(DynamicLink).filter(
            DynamicLink.short_code == link_short_code,
            DynamicLink.project_id == project.id
        ).first()
        
        if not link:
            raise HTTPException(status_code=404, detail="Lien non trouvé")
        
        referral_code = None
        if link.link_type == "referral":
            referral = db.query(ReferralCode).filter(
                ReferralCode.code == link.short_code,
                ReferralCode.project_id == link.project_id
            ).first()
            if referral:
                referral_code = referral.code
        
        return {
            "id": str(link.id),
            "short_code": link.short_code,
            "original_url": link.original_url,
            "title": link.title,
            "description": link.description,
            "referral_code": referral_code,
            "utm_params": {
                "utm_source": link.utm_source,
                "utm_medium": link.utm_medium,
                "utm_campaign": link.utm_campaign,
                "utm_term": link.utm_term,
                "utm_content": link.utm_content,
            } if any([link.utm_source, link.utm_medium, link.utm_campaign, link.utm_term, link.utm_content]) else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sdk/referral/{referral_code}")
async def get_referral_data(
    *,
    referral_code: str,
    project_id: str,
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Récupère les données d'un code de parrainage pour le SDK
    """
    try:
        # Valider l'accès au projet
        project = await validate_project_access(project_id, api_key, db)
        
        referral = db.query(ReferralCode).filter(
            ReferralCode.code == referral_code,
            ReferralCode.project_id == project.id
        ).first()
        
        if not referral:
            raise HTTPException(status_code=404, detail="Code de parrainage non trouvé")
        
        return {
            "code": referral.code,
            "reward_type": referral.reward_type,
            "reward_value": float(referral.reward_value),
            "max_uses": referral.max_uses,
            "current_uses": referral.current_uses,
            "is_active": referral.is_active,
            "expires_at": referral.expires_at.isoformat() if referral.expires_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
