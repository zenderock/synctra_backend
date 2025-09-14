from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.sdk_auth import get_api_key_auth
from app.models.project import Project
from app.models.dynamic_link import DynamicLink
from app.schemas.sdk import (
    DeepLinkCreate, 
    DeepLinkUpdate, 
    DeepLinkResponse, 
    SDKResponse,
    PaginatedResponse,
    AnalyticsResponse
)
from app.services.link_generator import LinkGenerator
from app.core.config import settings

router = APIRouter()

@router.post("", status_code=201, include_in_schema=False)
@router.post("/", status_code=201)
async def create_link(
    link_data: DeepLinkCreate,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Créer un nouveau lien dynamique."""
    
    short_code = LinkGenerator.generate_unique_short_code(db)
    
    # Construire l'URL finale avec les paramètres
    final_url = str(link_data.originalUrl)
    if link_data.parameters:
        utm_params = {}
        for key, value in link_data.parameters.items():
            if key.startswith('utm_'):
                utm_params[key] = value
        if utm_params:
            final_url = LinkGenerator.build_utm_url(final_url, utm_params)
    
    link = DynamicLink(
        project_id=project.id,
        short_code=short_code,
        original_url=final_url,
        title=link_data.metadata.get('title') if link_data.metadata else None,
        description=link_data.metadata.get('description') if link_data.metadata else None,
        android_fallback_url=link_data.androidPlayStoreUrl,
        ios_fallback_url=link_data.iosAppStoreUrl,
        desktop_fallback_url=link_data.fallbackUrl,
        expires_at=link_data.expiresAt,
        created_by=None  # SDK n'a pas d'utilisateur connecté
    )
    
    db.add(link)
    db.commit()
    db.refresh(link)
    
    short_url = LinkGenerator.build_short_url(
        link.short_code, 
        project.custom_domain or settings.DOMAIN
    )
    
    return SDKResponse(
        success=True,
        data=DeepLinkResponse(
            id=str(link.id),
            originalUrl=link.original_url,
            shortUrl=short_url,
            parameters=link_data.parameters,
            fallbackUrl=link.desktop_fallback_url,
            iosAppStoreUrl=link.ios_fallback_url,
            androidPlayStoreUrl=link.android_fallback_url,
            createdAt=link.created_at,
            expiresAt=link.expires_at,
            isActive=link.is_active,
            campaignId=link_data.campaignId,
            referralCode=link_data.referralCode
        )
    )

@router.get("/{linkId}")
async def get_link(
    linkId: str,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Récupérer un lien spécifique."""
    
    link = db.query(DynamicLink).filter(
        DynamicLink.id == linkId,
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
    
    short_url = LinkGenerator.build_short_url(
        link.short_code, 
        project.custom_domain or settings.DOMAIN
    )
    
    return SDKResponse(
        success=True,
        data=DeepLinkResponse(
            id=str(link.id),
            originalUrl=link.original_url,
            shortUrl=short_url,
            parameters={},  # TODO: extraire des paramètres stockés
            fallbackUrl=link.desktop_fallback_url,
            iosAppStoreUrl=link.ios_fallback_url,
            androidPlayStoreUrl=link.android_fallback_url,
            createdAt=link.created_at,
            expiresAt=link.expires_at,
            isActive=link.is_active,
            campaignId=None,  # TODO: ajouter campaign_id au modèle
            referralCode=None  # TODO: ajouter referral_code au modèle
        )
    )

@router.get("", include_in_schema=False)
@router.get("/")
async def list_links(
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    campaignId: Optional[str] = Query(None),
    isActive: Optional[bool] = Query(None)
):
    """Lister les liens avec filtres optionnels."""
    
    query = db.query(DynamicLink).filter(DynamicLink.project_id == project.id)
    
    if isActive is not None:
        query = query.filter(DynamicLink.is_active == isActive)
    
    # TODO: Ajouter filtre campaignId quand le champ sera ajouté
    
    total = query.count()
    links = query.offset(offset).limit(limit).all()
    
    link_responses = []
    for link in links:
        short_url = LinkGenerator.build_short_url(
            link.short_code, 
            project.custom_domain or settings.DOMAIN
        )
        
        link_responses.append(DeepLinkResponse(
            id=str(link.id),
            originalUrl=link.original_url,
            shortUrl=short_url,
            parameters={},
            fallbackUrl=link.desktop_fallback_url,
            iosAppStoreUrl=link.ios_fallback_url,
            androidPlayStoreUrl=link.android_fallback_url,
            createdAt=link.created_at,
            expiresAt=link.expires_at,
            isActive=link.is_active,
            campaignId=None,
            referralCode=None
        ))
    
    return SDKResponse(
        success=True,
        data=PaginatedResponse(
            links=link_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    )

@router.put("/{linkId}")
async def update_link(
    linkId: str,
    link_data: DeepLinkUpdate,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Mettre à jour un lien existant."""
    
    link = db.query(DynamicLink).filter(
        DynamicLink.id == linkId,
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
    
    update_data = link_data.dict(exclude_unset=True)
    
    # Mapper les champs SDK vers les champs du modèle
    field_mapping = {
        'originalUrl': 'original_url',
        'fallbackUrl': 'desktop_fallback_url',
        'iosAppStoreUrl': 'ios_fallback_url',
        'androidPlayStoreUrl': 'android_fallback_url',
        'expiresAt': 'expires_at',
        'isActive': 'is_active'
    }
    
    for sdk_field, db_field in field_mapping.items():
        if sdk_field in update_data:
            setattr(link, db_field, update_data[sdk_field])
    
    db.commit()
    db.refresh(link)
    
    short_url = LinkGenerator.build_short_url(
        link.short_code, 
        project.custom_domain or settings.DOMAIN
    )
    
    return SDKResponse(
        success=True,
        data=DeepLinkResponse(
            id=str(link.id),
            originalUrl=link.original_url,
            shortUrl=short_url,
            parameters=link_data.parameters or {},
            fallbackUrl=link.desktop_fallback_url,
            iosAppStoreUrl=link.ios_fallback_url,
            androidPlayStoreUrl=link.android_fallback_url,
            createdAt=link.created_at,
            expiresAt=link.expires_at,
            isActive=link.is_active,
            campaignId=link_data.campaignId,
            referralCode=link_data.referralCode
        )
    )

@router.delete("/{linkId}", status_code=204)
async def delete_link(
    linkId: str,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Supprimer un lien."""
    
    link = db.query(DynamicLink).filter(
        DynamicLink.id == linkId,
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
    
    db.delete(link)
    db.commit()

@router.get("/{linkId}/analytics")
async def get_link_analytics(
    linkId: str,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db),
    startDate: Optional[datetime] = Query(None),
    endDate: Optional[datetime] = Query(None)
):
    """Récupérer les analytics d'un lien."""
    
    link = db.query(DynamicLink).filter(
        DynamicLink.id == linkId,
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
    
    # TODO: Implémenter la logique d'analytics réelle
    # Pour l'instant, retourner des données de base
    
    return SDKResponse(
        success=True,
        data=AnalyticsResponse(
            totalClicks=len(link.clicks) if link.clicks else 0,
            uniqueClicks=0,  # TODO: calculer les clics uniques
            conversions=0,   # TODO: calculer les conversions
            platforms={},    # TODO: grouper par plateforme
            countries={},    # TODO: grouper par pays
            timeline=[]      # TODO: données temporelles
        )
    )
