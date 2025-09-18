from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/{project_id}/links", response_model=List[schemas.DynamicLink])
def read_project_links(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Récupérer les liens avec leurs statistiques en une seule requête optimisée
    links_with_stats = db.query(
        models.DynamicLink,
        func.count(models.LinkClick.id).label('clicks'),
        func.sum(case((models.LinkClick.converted == True, 1), else_=0)).label('conversions')
    ).outerjoin(models.LinkClick).filter(
        models.DynamicLink.project_id == project_id
    ).group_by(models.DynamicLink.id).all()
    
    # Enrichir les liens avec l'URL courte complète et les statistiques
    base_url = "https://link.synctra.com"  # TODO: Récupérer depuis la config
    enriched_links = []
    
    for link_data in links_with_stats:
        link = link_data[0]  # L'objet DynamicLink
        clicks = link_data[1] or 0  # Nombre de clics
        conversions = link_data[2] or 0  # Nombre de conversions
        
        # Construire l'URL courte complète
        short_url = f"{base_url}/{link.short_code}"
        
        # Créer un objet enrichi
        link_dict = {
            "id": str(link.id),
            "project_id": str(link.project_id),
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
            "link_type": link.link_type,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "is_active": link.is_active,
            "clicks": clicks,
            "conversions": conversions,
            "created_by": str(link.created_by),
            "created_at": link.created_at.isoformat(),
            "updated_at": link.updated_at.isoformat()
        }
        enriched_links.append(link_dict)
    
    return enriched_links


@router.post("/{project_id}/links", response_model=schemas.DynamicLink)
def create_project_link(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    link_in: schemas.DynamicLinkCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Vérifier les limites du plan
    organization = crud.organization.get(db, id=current_user.organization_id)
    limits = crud.organization.get_plan_limits(organization.plan_type)
    current_links = crud.dynamic_link.count_by_project(db, project_id=project_id)
    
    if limits["max_links_per_project"] != -1 and current_links >= limits["max_links_per_project"]:
        raise HTTPException(
            status_code=402, 
            detail=f"Limite de liens atteinte pour le plan {organization.plan_type}"
        )
    
    link = crud.dynamic_link.create(
        db, 
        obj_in=link_in, 
        project_id=project_id, 
        created_by=str(current_user.id)
    )
    
    base_url = "https://synctra.link"
    short_url = f"{base_url}/{link.short_code}"
    
    link_dict = {
        "id": str(link.id),
        "project_id": str(link.project_id),
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
        "link_type": link.link_type,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        "is_active": link.is_active,
        "clicks": 0,
        "conversions": 0,
        "created_by": str(link.created_by),
        "created_at": link.created_at.isoformat(),
        "updated_at": link.updated_at.isoformat()
    }
    
    return link_dict


@router.get("/{project_id}/links/{link_id}", response_model=schemas.DynamicLink)
def read_project_link(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    link_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    link = crud.dynamic_link.get(db, id=link_id)
    if not link or str(link.project_id) != project_id:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    # Enrichir avec les statistiques pour la réponse
    clicks_count = db.query(func.count(models.LinkClick.id)).filter(
        models.LinkClick.link_id == link.id
    ).scalar() or 0
    
    conversions_count = db.query(func.count(models.LinkClick.id)).filter(
        models.LinkClick.link_id == link.id,
        models.LinkClick.converted == True
    ).scalar() or 0
    
    # Construire l'URL courte complète
    base_url = "https://link.synctra.com"
    short_url = f"{base_url}/{link.short_code}"
    
    # Créer un objet enrichi pour la réponse
    link_dict = {
        "id": str(link.id),
        "project_id": str(link.project_id),
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
        "link_type": link.link_type,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        "is_active": link.is_active,
        "clicks": clicks_count,
        "conversions": conversions_count,
        "created_by": str(link.created_by),
        "created_at": link.created_at.isoformat(),
        "updated_at": link.updated_at.isoformat()
    }
    
    return link_dict


@router.put("/{project_id}/links/{link_id}", response_model=schemas.DynamicLink)
def update_project_link(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    link_id: str,
    link_in: schemas.DynamicLinkUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    link = crud.dynamic_link.get(db, id=link_id)
    if not link or str(link.project_id) != project_id:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    link = crud.dynamic_link.update(db, db_obj=link, obj_in=link_in)
    
    # Enrichir avec les statistiques pour la réponse
    clicks_count = db.query(func.count(models.LinkClick.id)).filter(
        models.LinkClick.link_id == link.id
    ).scalar() or 0
    
    conversions_count = db.query(func.count(models.LinkClick.id)).filter(
        models.LinkClick.link_id == link.id,
        models.LinkClick.converted == True
    ).scalar() or 0
    
    # Construire l'URL courte complète
    base_url = "https://link.synctra.com"
    short_url = f"{base_url}/{link.short_code}"
    
    # Créer un objet enrichi pour la réponse
    link_dict = {
        "id": str(link.id),
        "project_id": str(link.project_id),
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
        "link_type": link.link_type,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        "is_active": link.is_active,
        "clicks": clicks_count,
        "conversions": conversions_count,
        "created_by": str(link.created_by),
        "created_at": link.created_at.isoformat(),
        "updated_at": link.updated_at.isoformat()
    }
    
    return link_dict


@router.delete("/{project_id}/links/{link_id}")
def delete_project_link(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    link_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    link = crud.dynamic_link.get(db, id=link_id)
    if not link or str(link.project_id) != project_id:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    crud.dynamic_link.remove(db, id=link_id)
    return {"message": "Lien supprimé avec succès"}
