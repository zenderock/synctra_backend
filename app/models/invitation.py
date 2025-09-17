from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='member')  # member, admin
    token = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default='pending')  # pending, accepted, expired, cancelled
    
    # Relations
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    accepted_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relations
    organization = relationship("Organization", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_id])
