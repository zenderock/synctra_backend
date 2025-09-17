from typing import Optional, List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.invitation import Invitation
from app.schemas.invitation import InvitationCreate, InvitationUpdate
from datetime import datetime, timezone, timedelta


class CRUDInvitation(CRUDBase[Invitation, InvitationCreate, InvitationUpdate]):
    def get_by_email_and_organization(
        self, db: Session, *, email: str, organization_id: str
    ) -> Optional[Invitation]:
        return db.query(Invitation).filter(
            Invitation.email == email,
            Invitation.organization_id == organization_id
        ).first()

    def get_by_token(self, db: Session, *, token: str) -> Optional[Invitation]:
        return db.query(Invitation).filter(Invitation.token == token).first()

    def get_by_organization(self, db: Session, *, organization_id: str) -> List[Invitation]:
        return db.query(Invitation).filter(Invitation.organization_id == organization_id).all()

    def create(
        self, 
        db: Session, 
        *, 
        obj_in: InvitationCreate, 
        organization_id: str,
        invited_by_id: str,
        token: str
    ) -> Invitation:
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        db_obj = Invitation(
            email=obj_in.email,
            role=obj_in.role,
            token=token,
            organization_id=organization_id,
            invited_by_id=invited_by_id,
            expires_at=expires_at
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_pending_invitations(self, db: Session, *, organization_id: str) -> List[Invitation]:
        return db.query(Invitation).filter(
            Invitation.organization_id == organization_id,
            Invitation.status == "pending"
        ).all()

    def get_expired_invitations(self, db: Session) -> List[Invitation]:
        now = datetime.now(timezone.utc)
        return db.query(Invitation).filter(
            Invitation.status == "pending",
            Invitation.expires_at < now
        ).all()


invitation = CRUDInvitation(Invitation)
