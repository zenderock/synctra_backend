from typing import List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.link_click import LinkClick
from app.schemas.link_click import LinkClickCreate, LinkClickUpdate


class CRUDLinkClick(CRUDBase[LinkClick, LinkClickCreate, LinkClickUpdate]):
    def get_by_link(self, db: Session, *, link_id: str) -> List[LinkClick]:
        return db.query(LinkClick).filter(LinkClick.link_id == link_id).all()

    def count_by_link(self, db: Session, *, link_id: str) -> int:
        return db.query(LinkClick).filter(LinkClick.link_id == link_id).count()

    def create_click(self, db: Session, *, obj_in: LinkClickCreate, link_id: str) -> LinkClick:
        db_obj = LinkClick(
            link_id=link_id,
            **obj_in.dict()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


link_click = CRUDLinkClick(LinkClick)
