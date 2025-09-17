from typing import Optional, List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
import secrets
from datetime import datetime


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def get_by_organization(self, db: Session, *, organization_id: str) -> List[Project]:
        return db.query(Project).filter(Project.organization_id == organization_id).all()

    def get_by_api_key(self, db: Session, *, api_key: str) -> Optional[Project]:
        return db.query(Project).filter(Project.api_key == api_key).first()

    def create(self, db: Session, *, obj_in: ProjectCreate, organization_id: str) -> Project:
        project_id = f"{obj_in.name.lower().replace(' ', '_')}_{datetime.now().year}"
        api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        
        db_obj = Project(
            name=obj_in.name,
            description=obj_in.description,
            project_id=project_id,
            organization_id=organization_id,
            api_key=api_key,
            custom_domain=obj_in.custom_domain,
            status=obj_in.status,
            settings=obj_in.settings or {}
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def count_by_organization(self, db: Session, *, organization_id: str) -> int:
        return db.query(Project).filter(Project.organization_id == organization_id).count()

    def can_access(self, db: Session, *, project: Project, user_id: str) -> bool:
        """
        Vérifier si un utilisateur a accès à un projet via son organisation
        """
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        return str(project.organization_id) == str(user.organization_id)

    def regenerate_api_key(self, db: Session, *, db_obj: Project) -> Project:
        """
        Régénère la clé API d'un projet
        """
        new_api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        db_obj.api_key = new_api_key
        db.commit()
        db.refresh(db_obj)
        return db_obj


project = CRUDProject(Project)
