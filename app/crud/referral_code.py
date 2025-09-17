from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.referral_code import ReferralCode
from app.schemas.referral_code import ReferralCodeCreate, ReferralCodeUpdate


class CRUDReferralCode(CRUDBase[ReferralCode, ReferralCodeCreate, ReferralCodeUpdate]):
    def get_by_project(
        self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100
    ) -> List[ReferralCode]:
        return (
            db.query(self.model)
            .filter(ReferralCode.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_code(self, db: Session, *, code: str) -> Optional[ReferralCode]:
        return db.query(self.model).filter(ReferralCode.code == code).first()
    
    def get_by_user_and_project(
        self, db: Session, *, user_id: str, project_id: str
    ) -> List[ReferralCode]:
        return (
            db.query(self.model)
            .filter(
                and_(
                    ReferralCode.user_id == user_id,
                    ReferralCode.project_id == project_id
                )
            )
            .all()
        )
    
    def increment_usage(self, db: Session, *, referral_code: ReferralCode) -> ReferralCode:
        referral_code.current_uses += 1
        db.add(referral_code)
        db.commit()
        db.refresh(referral_code)
        return referral_code


referral_code = CRUDReferralCode(ReferralCode)
