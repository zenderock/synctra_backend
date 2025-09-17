from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
import re


class CRUDOrganization(CRUDBase[Organization, OrganizationCreate, OrganizationUpdate]):
    def get_by_slug(self, db: Session, *, slug: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.slug == slug).first()

    def create(self, db: Session, *, obj_in: OrganizationCreate) -> Organization:
        slug = self._generate_slug(obj_in.name)
        print(f"DEBUG CRUD: Création avec name='{obj_in.name}', slug='{slug}'")
        
        db_obj = Organization(
            name=obj_in.name,
            slug=slug,
            domain=obj_in.domain,
            plan_type=obj_in.plan_type,
            settings={}
        )
        
        print(f"DEBUG CRUD: Objet créé - name='{db_obj.name}', slug='{db_obj.slug}'")
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        print(f"DEBUG CRUD: Après commit - name='{db_obj.name}', slug='{db_obj.slug}'")
        
        return db_obj

    def _generate_slug(self, name: str) -> str:
        slug = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        return slug

    def get_plan_limits(self, plan_type: str) -> dict:
        limits = {
            'free': {
                'max_projects': 1,
                'max_links_per_project': 5,
                'max_members': 1
            },
            'pro': {
                'max_projects': 4,
                'max_links_per_project': 100,
                'max_members': 5
            },
            'plus': {
                'max_projects': -1,  # illimité
                'max_links_per_project': -1,  # illimité
                'max_members': 20
            }
        }
        return limits.get(plan_type, limits['free'])


organization = CRUDOrganization(Organization)
