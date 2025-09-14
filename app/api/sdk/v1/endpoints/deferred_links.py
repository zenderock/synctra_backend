from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.sdk_auth import get_api_key_auth
from app.models.project import Project
from app.models.dynamic_link import DynamicLink
from app.models.deferred_link import DeferredLink
from app.schemas.sdk import DeferredLinkCreate, DeferredLinkQuery, SDKResponse, DeepLinkResponse
from app.services.link_generator import LinkGenerator
from app.core.config import settings

router = APIRouter()

@router.get("", include_in_schema=False)
@router.get("/")
async def get_deferred_link(
    packageName: str = Query(..., description="Nom du package"),
    deviceId: str = Query(..., description="ID de l'appareil"),
    platform: str = Query(..., description="Plateforme"),
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Récupérer un lien différé pour un appareil."""
    
    # Chercher un lien différé non consommé et non expiré
    deferred_link = db.query(DeferredLink).filter(
        DeferredLink.device_id == deviceId,
        DeferredLink.package_name == packageName,
        DeferredLink.platform == platform,
        DeferredLink.is_consumed == False,
        DeferredLink.expires_at > datetime.utcnow()
    ).order_by(DeferredLink.created_at.desc()).first()
    
    if not deferred_link:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Aucun lien différé trouvé",
                "code": "NO_DEFERRED_LINK"
            }
        )
    
    # Marquer comme consommé
    deferred_link.is_consumed = True
    deferred_link.consumed_at = datetime.utcnow()
    db.commit()
    
    # Retourner les données du lien
    return DeepLinkResponse(
        success=True,
        data={
            "id": deferred_link.link_id,
            "originalUrl": deferred_link.original_url,
            "parameters": deferred_link.parameters or {},
            "timestamp": deferred_link.timestamp.isoformat(),
            "consumed": True
        }
    )

@router.post("", status_code=201, include_in_schema=False)
@router.post("/", status_code=201)
async def store_deferred_link(
    deferred_data: DeferredLinkCreate,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Stocker des données de lien différé."""
    
    # Vérifier que le lien existe dans ce projet
    link = db.query(DynamicLink).filter(
        DynamicLink.id == deferred_data.linkId,
        DynamicLink.project_id == project.id
    ).first()
    
    if not link:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Lien non trouvé",
                "code": "LINK_NOT_FOUND"
            }
        )
    
    # Supprimer les anciens liens différés pour ce device (éviter les doublons)
    db.query(DeferredLink).filter(
        DeferredLink.device_id == deferred_data.deviceId,
        DeferredLink.package_name == deferred_data.packageName,
        DeferredLink.platform == deferred_data.platform
    ).delete()
    
    # Créer le nouveau lien différé
    deferred_link = DeferredLink(
        device_id=deferred_data.deviceId,
        package_name=deferred_data.packageName,
        platform=deferred_data.platform,
        link_id=deferred_data.linkId,
        original_url=str(link.original_url),
        parameters=deferred_data.parameters or {},
        ip_address=getattr(deferred_data, 'metadata', {}).get('ip_address'),
        user_agent=getattr(deferred_data, 'metadata', {}).get('userAgent'),
        timestamp=datetime.fromisoformat(deferred_data.timestamp.replace('Z', '+00:00')),
        expires_at=datetime.utcnow() + timedelta(hours=24)  # Expire après 24h
    )
    
    db.add(deferred_link)
    db.commit()
    db.refresh(deferred_link)
    
    return SDKResponse(success=True)

@router.delete("", status_code=204, include_in_schema=False)
@router.delete("/", status_code=204)
async def clean_deferred_link(
    packageName: str = Query(..., description="Nom du package"),
    deviceId: str = Query(..., description="ID de l'appareil"),
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Nettoyer les données de lien différé."""
    
    # Supprimer tous les liens différés pour ce device
    deleted_count = db.query(DeferredLink).filter(
        DeferredLink.device_id == deviceId,
        DeferredLink.package_name == packageName
    ).delete()
    
    db.commit()
    
    return {"deleted": deleted_count}
