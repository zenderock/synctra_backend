from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_project_by_id
from app.models.user import User
from app.models.project import Project
from app.models.dynamic_link import DynamicLink
from app.schemas.dynamic_link import DynamicLinkCreate, DynamicLinkUpdate, DynamicLinkResponse
from app.schemas.response import ApiResponse
from app.services.link_generator import LinkGenerator
from app.core.config import settings
from app.core.exceptions import ValidationException, NotFoundException
from app.services.subscription_service import SubscriptionService

router = APIRouter()

@router.get("/")
async def get_links(
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    links = db.query(DynamicLink).filter(
        DynamicLink.project_id == project.id
    ).offset(skip).limit(limit).all()
    
    links_data = []
    for link in links:
        short_url = LinkGenerator.build_short_url(
            link.short_code, 
            project.custom_domain or settings.DOMAIN
        )
        links_data.append({
            "id": str(link.id),
            "short_code": link.short_code,
            "short_url": short_url,
            "original_url": link.original_url,
            "title": link.title,
            "description": link.description,
            "android_package": link.android_package,
            "android_fallback_url": link.android_fallback_url,
            "ios_bundle_id": link.ios_bundle_id,
            "ios_fallback_url": link.ios_fallback_url,
            "desktop_fallback_url": link.desktop_fallback_url,
            "utm_source": link.utm_source,
            "utm_medium": link.utm_medium,
            "utm_campaign": link.utm_campaign,
            "utm_term": link.utm_term,
            "utm_content": link.utm_content,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "is_active": link.is_active,
            "click_count": len(link.clicks) if link.clicks else 0,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "updated_at": link.updated_at.isoformat() if link.updated_at else None
        })
    
    return ApiResponse.success(
        data=links_data,
        message="Liens récupérés avec succès"
    )

@router.post("/")
async def create_link(
    link_data: DynamicLinkCreate,
    project: Project = Depends(get_project_by_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Vérifier les limites de liens pour le projet
    if not SubscriptionService.check_links_limit(db, str(project.id)):
        return ApiResponse.error(
            message="Limite de liens atteinte pour ce projet selon votre plan actuel.",
            status_code=429
        )
    
    short_code = LinkGenerator.generate_unique_short_code(db)
    
    utm_params = {}
    if link_data.utm_source:
        utm_params['utm_source'] = link_data.utm_source
    if link_data.utm_medium:
        utm_params['utm_medium'] = link_data.utm_medium
    if link_data.utm_campaign:
        utm_params['utm_campaign'] = link_data.utm_campaign
    if link_data.utm_term:
        utm_params['utm_term'] = link_data.utm_term
    if link_data.utm_content:
        utm_params['utm_content'] = link_data.utm_content
    
    final_url = LinkGenerator.build_utm_url(str(link_data.original_url), utm_params)
    
    link = DynamicLink(
        project_id=project.id,
        short_code=short_code,
        original_url=final_url,
        title=link_data.title,
        description=link_data.description,
        android_package=link_data.android_package,
        android_fallback_url=str(link_data.android_fallback_url) if link_data.android_fallback_url else None,
        ios_bundle_id=link_data.ios_bundle_id,
        ios_fallback_url=str(link_data.ios_fallback_url) if link_data.ios_fallback_url else None,
        desktop_fallback_url=str(link_data.desktop_fallback_url) if link_data.desktop_fallback_url else None,
        utm_source=link_data.utm_source,
        utm_medium=link_data.utm_medium,
        utm_campaign=link_data.utm_campaign,
        utm_term=link_data.utm_term,
        utm_content=link_data.utm_content,
        expires_at=link_data.expires_at,
        created_by=current_user.id
    )
    
    db.add(link)
    db.commit()
    db.refresh(link)
    
    short_url = LinkGenerator.build_short_url(
        link.short_code, 
        project.custom_domain or settings.DOMAIN
    )
    
    return ApiResponse.success(
        data={
            "id": str(link.id),
            "short_code": link.short_code,
            "short_url": short_url,
            "original_url": link.original_url,
            "title": link.title,
            "description": link.description,
            "android_package": link.android_package,
            "android_fallback_url": link.android_fallback_url,
            "ios_bundle_id": link.ios_bundle_id,
            "ios_fallback_url": link.ios_fallback_url,
            "desktop_fallback_url": link.desktop_fallback_url,
            "utm_source": link.utm_source,
            "utm_medium": link.utm_medium,
            "utm_campaign": link.utm_campaign,
            "utm_term": link.utm_term,
            "utm_content": link.utm_content,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "is_active": link.is_active,
            "click_count": len(link.clicks) if link.clicks else 0,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "updated_at": link.updated_at.isoformat() if link.updated_at else None
        },
        message="Lien créé avec succès"
    )

@router.get("/{link_id}")
async def get_link(
    link_id: str,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    link = db.query(DynamicLink).filter(
        DynamicLink.id == link_id,
        DynamicLink.project_id == project.id
    ).first()
    
    if not link:
        return ApiResponse.error(
            message="Lien non trouvé",
            status_code=404
        )
    
    short_url = LinkGenerator.build_short_url(
        link.short_code, 
        project.custom_domain or settings.DOMAIN
    )
    
    return ApiResponse.success(
        data={
            "id": str(link.id),
            "short_code": link.short_code,
            "short_url": short_url,
            "original_url": link.original_url,
            "title": link.title,
            "description": link.description,
            "android_package": link.android_package,
            "android_fallback_url": link.android_fallback_url,
            "ios_bundle_id": link.ios_bundle_id,
            "ios_fallback_url": link.ios_fallback_url,
            "desktop_fallback_url": link.desktop_fallback_url,
            "utm_source": link.utm_source,
            "utm_medium": link.utm_medium,
            "utm_campaign": link.utm_campaign,
            "utm_term": link.utm_term,
            "utm_content": link.utm_content,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "is_active": link.is_active,
            "click_count": len(link.clicks) if link.clicks else 0,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "updated_at": link.updated_at.isoformat() if link.updated_at else None
        },
        message="Lien récupéré avec succès"
    )

@router.put("/{link_id}")
async def update_link(
    link_id: str,
    link_data: DynamicLinkUpdate,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    link = db.query(DynamicLink).filter(
        DynamicLink.id == link_id,
        DynamicLink.project_id == project.id
    ).first()
    
    if not link:
        return ApiResponse.error(
            message="Lien non trouvé",
            status_code=404
        )
    
    update_data = link_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field.endswith('_url') and value:
            value = str(value)
        setattr(link, field, value)
    
    db.commit()
    db.refresh(link)
    
    short_url = LinkGenerator.build_short_url(
        link.short_code, 
        project.custom_domain or settings.DOMAIN
    )
    
    return ApiResponse.success(
        data={
            "id": str(link.id),
            "short_code": link.short_code,
            "short_url": short_url,
            "original_url": link.original_url,
            "title": link.title,
            "description": link.description,
            "android_package": link.android_package,
            "android_fallback_url": link.android_fallback_url,
            "ios_bundle_id": link.ios_bundle_id,
            "ios_fallback_url": link.ios_fallback_url,
            "desktop_fallback_url": link.desktop_fallback_url,
            "utm_source": link.utm_source,
            "utm_medium": link.utm_medium,
            "utm_campaign": link.utm_campaign,
            "utm_term": link.utm_term,
            "utm_content": link.utm_content,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "is_active": link.is_active,
            "click_count": len(link.clicks) if link.clicks else 0,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "updated_at": link.updated_at.isoformat() if link.updated_at else None
        },
        message="Lien mis à jour avec succès"
    )

@router.delete("/{link_id}")
async def delete_link(
    link_id: str,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    link = db.query(DynamicLink).filter(
        DynamicLink.id == link_id,
        DynamicLink.project_id == project.id
    ).first()
    
    if not link:
        return ApiResponse.error(
            message="Lien non trouvé",
            status_code=404
        )
    
    db.delete(link)
    db.commit()
    
    return ApiResponse.success(
        message="Lien supprimé avec succès"
    )
