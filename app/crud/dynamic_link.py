from typing import Optional, List
import secrets
import string
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.dynamic_link import DynamicLink
from app.schemas.dynamic_link import DynamicLinkCreate, DynamicLinkUpdate


class CRUDDynamicLink(CRUDBase[DynamicLink, DynamicLinkCreate, DynamicLinkUpdate]):
    def get_by_project(self, db: Session, *, project_id: str) -> List[DynamicLink]:
        return db.query(DynamicLink).filter(DynamicLink.project_id == project_id).all()

    def get_by_short_code(self, db: Session, *, short_code: str) -> Optional[DynamicLink]:
        return db.query(DynamicLink).filter(DynamicLink.short_code == short_code).first()

    def _generate_short_code(self, db: Session, length: int = 6) -> str:
        """Génère un code court unique"""
        while True:
            code = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
            if not self.get_by_short_code(db, short_code=code):
                return code

    def create(self, db: Session, *, obj_in: DynamicLinkCreate, project_id: str, created_by: str) -> DynamicLink:
        # Générer un short_code unique
        short_code = self._generate_short_code(db)
        
        db_obj = DynamicLink(
            project_id=project_id,
            created_by=created_by,
            short_code=short_code,
            **obj_in.dict()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def count_by_project(self, db: Session, *, project_id: str) -> int:
        return db.query(DynamicLink).filter(DynamicLink.project_id == project_id).count()

    def get_active_by_project(self, db: Session, *, project_id: str) -> List[DynamicLink]:
        return db.query(DynamicLink).filter(
            DynamicLink.project_id == project_id,
            DynamicLink.is_active == True
        ).all()


dynamic_link = CRUDDynamicLink(DynamicLink)
