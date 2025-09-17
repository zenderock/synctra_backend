from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.post("/", response_model=schemas.Organization)
def create_organization(
    *,
    db: Session = Depends(deps.get_db),
    organization_in: schemas.OrganizationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    # Vérifier que l'utilisateur n'a pas déjà une organisation
    if current_user.organization_id:
        raise HTTPException(status_code=400, detail="Vous êtes déjà membre d'une organisation")
    
    # Debug: Log les données reçues
    print(f"DEBUG: Création organisation avec name='{organization_in.name}', plan_type='{organization_in.plan_type}'")
    
    # Créer l'organisation
    organization = crud.organization.create(db, obj_in=organization_in)
    
    # Debug: Log l'organisation créée
    print(f"DEBUG: Organisation créée - id={organization.id}, name='{organization.name}', slug='{organization.slug}'")
    
    # Associer l'utilisateur à l'organisation comme admin
    current_user.organization_id = organization.id
    current_user.role = "admin"
    db.commit()
    db.refresh(current_user)
    
    return organization


@router.get("/all", response_model=List[schemas.Organization])
def read_organizations(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    organizations = crud.organization.get_multi(db, skip=skip, limit=limit)
    return organizations


@router.get("/me", response_model=schemas.Organization)
def read_my_organization(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation associée")
    
    organization = crud.organization.get(db, id=current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    return organization


@router.put("/me", response_model=schemas.Organization)
def update_my_organization(
    *,
    db: Session = Depends(deps.get_db),
    organization_in: schemas.OrganizationUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation associée")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")
    
    organization = crud.organization.get(db, id=current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    organization = crud.organization.update(db, db_obj=organization, obj_in=organization_in)
    return organization


@router.get("/me/limits", response_model=dict)
def get_organization_limits(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation associée")
    
    organization = crud.organization.get(db, id=current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    limits = crud.organization.get_plan_limits(organization.plan_type)
    
    # Calculer l'utilisation actuelle
    current_projects = crud.project.count_by_organization(db, organization_id=str(organization.id))
    current_members = len(crud.user.get_by_organization(db, organization_id=str(organization.id)))
    
    return {
        "plan_type": organization.plan_type,
        "limits": limits,
        "current_usage": {
            "projects": current_projects,
            "members": current_members
        }
    }


@router.get("/me/stats", response_model=dict)
def get_organization_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation associée")
    
    organization = crud.organization.get(db, id=current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    # Récupérer tous les projets de l'organisation
    projects = crud.project.get_by_organization(db, organization_id=str(organization.id))
    
    # Calculer les statistiques
    total_projects = len(projects)
    active_projects = len([p for p in projects if p.status == 'production'])
    development_projects = len([p for p in projects if p.status == 'development'])
    
    # Calculer les statistiques réelles de liens et clics de manière optimisée
    total_links = 0
    total_clicks = 0
    
    for project in projects:
        # Compter les liens dynamiques de chaque projet
        project_links_count = crud.dynamic_link.count_by_project(db, project_id=str(project.id))
        total_links += project_links_count
        
        # Compter les clics pour tous les liens du projet
        project_links = crud.dynamic_link.get_by_project(db, project_id=str(project.id))
        for link in project_links:
            link_clicks_count = crud.link_click.count_by_link(db, link_id=str(link.id))
            total_clicks += link_clicks_count
    
    # Calculer les projets créés ce mois-ci
    from datetime import datetime, timezone
    current_month = datetime.now(timezone.utc).month
    current_year = datetime.now(timezone.utc).year
    
    projects_this_month = len([
        p for p in projects 
        if p.created_at.month == current_month and p.created_at.year == current_year
    ])
    
    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "development_projects": development_projects,
        "total_links": total_links,
        "total_clicks": total_clicks,
        "projects_this_month": projects_this_month,
        "organization_name": organization.name,
        "plan_type": organization.plan_type
    }


@router.post("/me/upgrade", response_model=schemas.Organization)
def upgrade_organization_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_type: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation associée")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")
    
    if plan_type not in ["free", "pro", "plus"]:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    organization = crud.organization.get(db, id=current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    organization_update = schemas.OrganizationUpdate(plan_type=plan_type)
    organization = crud.organization.update(db, db_obj=organization, obj_in=organization_update)
    
    return organization
