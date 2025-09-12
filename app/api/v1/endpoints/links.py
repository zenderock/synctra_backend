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
from app.services.link_generator import LinkGenerator
from app.core.config import settings
from app.core.exceptions import ValidationException, NotFoundException
from app.services.subscription_service import SubscriptionService

router = APIRouter()

@router.get("/", response_model=List[DynamicLinkResponse])
async def get_links(
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    links = db.query(DynamicLink).filter(
        DynamicLink.project_id == project.id
    ).offset(skip).limit(limit).all()
    
    for link in links:
        link.short_url = LinkGenerator.build_short_url(
            link.short_code, 
            project.custom_domain or settings.DOMAIN
        )
    
    return links

@router.post("/", response_model=DynamicLinkResponse)
async def create_link(
    link_data: DynamicLinkCreate,
    project: Project = Depends(get_project_by_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Vérifier les limites de liens pour le projet
    if not SubscriptionService.check_links_limit(db, str(project.id)):
        raise HTTPException(
            status_code=403,
            detail="Limite de liens atteinte pour ce projet selon votre plan actuel."
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
    
    link.short_url = LinkGenerator.build_short_url(
        link.short_code, 
        project.custom_domain or settings.DOMAIN
    )
    
    return link

@router.get("/{link_id}", response_model=DynamicLinkResponse)
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
        raise NotFoundException("Lien non trouvé")
    
    link.short_url = LinkGenerator.build_short_url(
        link.short_code, 
        project.custom_domain or settings.DOMAIN
    )
    
    return link

@router.put("/{link_id}", response_model=DynamicLinkResponse)
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
        raise NotFoundException("Lien non trouvé")
    
    update_data = link_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field.endswith('_url') and value:
            value = str(value)
        setattr(link, field, value)
    
    db.commit()
    db.refresh(link)
    
    link.short_url = LinkGenerator.build_short_url(
        link.short_code, 
        project.custom_domain or settings.DOMAIN
    )
    
    return link

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
        raise NotFoundException("Lien non trouvé")
    
    db.delete(link)
    db.commit()
    
    return {"message": "Lien supprimé avec succès"}
