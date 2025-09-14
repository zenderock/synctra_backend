from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets
import string

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_current_organization, get_project_by_id
from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.response import ApiResponse
from app.core.exceptions import ValidationException, NotFoundException
from app.services.subscription_service import SubscriptionService
from app.middleware.subscription_middleware import require_limit_check

router = APIRouter()

def generate_api_key() -> str:
    return f"sk_live_{''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))}"

def generate_project_id(name: str) -> str:
    base_id = name.lower().replace(" ", "_").replace("'", "")
    base_id = ''.join(c for c in base_id if c.isalnum() or c == '_')
    return f"{base_id[:20]}_2024"

@router.get("", include_in_schema=False)
@router.get("/")
async def get_projects(
    db: Session = Depends(get_db),
    current_organization: Organization = Depends(get_current_organization)
):
    projects = db.query(Project).filter(
        Project.organization_id == current_organization.id
    ).all()
    projects_data = []
    for project in projects:
        projects_data.append({
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "api_key": project.api_key,
            "custom_domain": project.custom_domain,
            "status": project.status,
            "is_active": project.is_active,
            "settings": project.settings or {},
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        })
    
    return ApiResponse.success(
        data=projects_data,
        message="Projets récupérés avec succès"
    )

@router.post("", include_in_schema=False)
@router.post("/")
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_organization: Organization = Depends(get_current_organization)
):
    # Vérifier les limites d'abonnement
    if not SubscriptionService.check_project_limit(db, str(current_organization.id)):
        return ApiResponse.error(
            message="Limite de projets atteinte pour votre plan actuel. Mettez à niveau votre abonnement.",
            status_code=429
        )
    
    # Vérifier l'accès au domaine personnalisé
    if project_data.custom_domain:
        if not SubscriptionService.has_feature_access(db, str(current_organization.id), "custom_domain"):
            return ApiResponse.error(
                message="Les domaines personnalisés nécessitent un plan Plus.",
                status_code=402
            )
    
    api_key = generate_api_key()
    
    project = Project(
        name=project_data.name,
        description=project_data.description,
        organization_id=current_organization.id,
        api_key=api_key,
        custom_domain=project_data.custom_domain,
        settings=project_data.settings or {}
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ApiResponse.success(
        data={
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "api_key": project.api_key,
            "custom_domain": project.custom_domain,
            "status": project.status,
            "is_active": project.is_active,
            "settings": project.settings or {},
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        },
        message="Projet créé avec succès"
    )

@router.get("/{project_id}")
async def get_project(
    project: Project = Depends(get_project_by_id)
):
    return ApiResponse.success(
        data={
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "api_key": project.api_key,
            "custom_domain": project.custom_domain,
            "status": project.status,
            "is_active": project.is_active,
            "settings": project.settings or {},
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        },
        message="Projet récupéré avec succès"
    )

@router.put("/{project_id}")
async def update_project(
    project_data: ProjectUpdate,
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    update_data = project_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return ApiResponse.success(
        data={
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "api_key": project.api_key,
            "custom_domain": project.custom_domain,
            "status": project.status,
            "is_active": project.is_active,
            "settings": project.settings or {},
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        },
        message="Projet mis à jour avec succès"
    )

@router.delete("/{project_id}")
async def delete_project(
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    db.delete(project)
    db.commit()
    
    return ApiResponse.success(
        message="Projet supprimé avec succès"
    )
