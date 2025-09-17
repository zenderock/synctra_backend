from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Project])
def read_projects(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation associée")
    
    projects = crud.project.get_by_organization(db, organization_id=str(current_user.organization_id))
    return projects


@router.post("/", response_model=schemas.Project)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation associée")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants pour créer un projet")
    
    # Vérifier les limites du plan
    organization = crud.organization.get(db, id=current_user.organization_id)
    limits = crud.organization.get_plan_limits(organization.plan_type)
    current_projects = crud.project.count_by_organization(db, organization_id=str(current_user.organization_id))
    
    if limits["max_projects"] != -1 and current_projects >= limits["max_projects"]:
        raise HTTPException(
            status_code=402, 
            detail=f"Limite de projets atteinte pour le plan {organization.plan_type}"
        )
    
    project = crud.project.create(db, obj_in=project_in, organization_id=str(current_user.organization_id))
    return project


@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
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
    
    return project


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    project_in: schemas.ProjectUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")
    
    project = crud.project.update(db, db_obj=project, obj_in=project_in)
    return project


@router.put("/{project_id}/app-config", response_model=schemas.Project)
def update_project_app_config(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    config_in: schemas.ProjectAppConfigUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Met à jour la configuration de l'application (package Android, bundle iOS, URLs)
    """
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")
    
    # Mettre à jour les champs de configuration de l'app
    update_data = config_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
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
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")
    
    crud.project.remove(db, id=project_id)
    return {"message": "Projet supprimé avec succès"}


@router.get("/{project_id}/stats", response_model=dict)
def get_project_stats(
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
    
    # Récupérer tous les liens du projet
    links = crud.dynamic_link.get_by_project(db, project_id=project_id)
    
    # Calculer les statistiques
    total_links = len(links)
    active_links = len([link for link in links if link.is_active])
    
    # Calculer les clics totaux (somme des clics de tous les liens)
    total_clicks = 0
    for link in links:
        clicks_count = db.query(models.LinkClick).filter(
            models.LinkClick.link_id == link.id
        ).count()
        total_clicks += clicks_count
    
    # Calculer les conversions réelles à partir des clics
    total_conversions = 0
    total_conversion_value = 0
    
    for link in links:
        # Compter les conversions pour ce lien
        conversions_count = db.query(models.LinkClick).filter(
            models.LinkClick.link_id == link.id,
            models.LinkClick.converted == True
        ).count()
        total_conversions += conversions_count
        
        # Calculer la valeur totale des conversions
        conversion_value_sum = db.query(func.sum(models.LinkClick.conversion_value)).filter(
            models.LinkClick.link_id == link.id,
            models.LinkClick.converted == True
        ).scalar() or 0
        total_conversion_value += float(conversion_value_sum)
    
    conversion_rate = round((total_conversions / total_clicks * 100), 2) if total_clicks > 0 else 0
    
    # Top 5 des liens les plus performants (par nombre de clics)
    links_with_clicks = []
    for link in links:
        link_clicks = db.query(models.LinkClick).filter(
            models.LinkClick.link_id == link.id
        ).count()
        links_with_clicks.append((link, link_clicks))
    
    # Trier par nombre de clics et prendre les 5 premiers
    top_links = sorted(links_with_clicks, key=lambda x: x[1], reverse=True)[:5]
    top_links_data = []
    for link, clicks_count in top_links:
        # Calculer les conversions réelles pour ce lien
        link_conversions = db.query(models.LinkClick).filter(
            models.LinkClick.link_id == link.id,
            models.LinkClick.converted == True
        ).count()
        
        # Construire l'URL courte à partir du short_code
        base_url = "https://link.synctra.com"  # TODO: Récupérer depuis la config
        short_url = f"{base_url}/{link.short_code}"
        
        top_links_data.append({
            "id": link.id,
            "title": link.title,
            "short_url": short_url,
            "clicks": clicks_count,
            "conversions": link_conversions
        })
    
    # Calculer les statistiques temporelles réelles
    from datetime import datetime, timezone, timedelta
    
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Compter les clics de la semaine pour tous les liens du projet
    clicks_this_week = db.query(models.LinkClick).join(models.DynamicLink).filter(
        models.DynamicLink.project_id == project_id,
        models.LinkClick.clicked_at >= week_ago
    ).count()
    
    # Compter les clics du mois pour tous les liens du projet
    clicks_this_month = db.query(models.LinkClick).join(models.DynamicLink).filter(
        models.DynamicLink.project_id == project_id,
        models.LinkClick.clicked_at >= month_ago
    ).count()
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_links": total_links,
        "active_links": active_links,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "conversion_rate": conversion_rate,
        "total_conversion_value": total_conversion_value,
        "clicks_this_week": clicks_this_week,
        "clicks_this_month": clicks_this_month,
        "top_links": top_links_data,
        "created_at": project.created_at,
        "last_updated": project.updated_at
    }


@router.post("/{project_id}/regenerate-api-key", response_model=schemas.Project)
def regenerate_project_api_key(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Régénère la clé API d'un projet
    """
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")
    
    # Régénérer la clé API
    project = crud.project.regenerate_api_key(db, db_obj=project)
    return project
