from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, DECIMAL, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class ReferralCode(BaseModel):
    __tablename__ = "referral_codes"
    
    code = Column(String(50), unique=True, nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    reward_type = Column(String(50))
    reward_value = Column(DECIMAL(10, 2))
    max_uses = Column(Integer)
    current_uses = Column(Integer, default=0)
    
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    project = relationship("Project", back_populates="referral_codes")
    user = relationship("User", back_populates="referral_codes")
    
    __table_args__ = (
        Index('idx_referral_project', 'project_id'),
        Index('idx_referral_code', 'code'),
    )
