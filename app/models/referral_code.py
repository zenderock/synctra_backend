from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index, DECIMAL, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Configuration
    reward_type = Column(String(50), nullable=False)  # percentage, fixed_amount, custom
    reward_value = Column(DECIMAL(10,2), nullable=True)
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0)
    
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="referral_codes")
    user = relationship("User", back_populates="created_referrals")

    __table_args__ = (
        Index('idx_referral_project', 'project_id'),
        Index('idx_referral_code', 'code'),
    )
