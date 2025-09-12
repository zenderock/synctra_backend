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

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    db: Session = Depends(get_db),
    current_organization: Organization = Depends(get_current_organization)
):
    projects = db.query(Project).filter(
        Project.organization_id == current_organization.id
    ).all()
    return projects

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_organization: Organization = Depends(get_current_organization)
):
    # Vérifier les limites d'abonnement
    if not SubscriptionService.check_project_limit(db, str(current_organization.id)):
        raise HTTPException(
            status_code=403,
            detail="Limite de projets atteinte pour votre plan actuel. Mettez à niveau votre abonnement."
        )
    
    # Vérifier l'accès au domaine personnalisé
    if project_data.custom_domain:
        if not SubscriptionService.has_feature_access(db, str(current_organization.id), "custom_domain"):
            raise HTTPException(
                status_code=403,
                detail="Les domaines personnalisés nécessitent un plan Plus."
            )
    
    project_id = generate_project_id(project_data.name)
    existing_project = db.query(Project).filter(Project.project_id == project_id).first()
    if existing_project:
        project_id = f"{project_id}_{secrets.token_hex(4)}"
    
    api_key = generate_api_key()
    
    project = Project(
        project_id=project_id,
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
    
    return project

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project: Project = Depends(get_project_by_id)
):
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
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
    
    return project

@router.delete("/{project_id}")
async def delete_project(
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db)
):
    db.delete(project)
    db.commit()
    
    return {"message": "Projet supprimé avec succès"}
