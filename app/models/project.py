from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import secrets
from datetime import datetime

from app.db.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    custom_domain = Column(String(255), nullable=True)
    status = Column(String(50), default='development')
    settings = Column(JSONB, default={})
    
    # Configuration globale de l'application
    android_package = Column(String(255), nullable=True)
    ios_bundle_id = Column(String(255), nullable=True)
    app_url = Column(String(500), nullable=True)
    android_fallback_url = Column(String(500), nullable=True)
    ios_fallback_url = Column(String(500), nullable=True)
    desktop_fallback_url = Column(String(500), nullable=True)
    assetlinks_json = Column(JSONB, nullable=True)
    apple_app_site_association = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization", back_populates="projects")
    dynamic_links = relationship("DynamicLink", back_populates="project")
    referral_codes = relationship("ReferralCode", back_populates="project")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.api_key:
            self.api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        if not self.project_id and self.name:
            self.project_id = f"{self.name.lower().replace(' ', '_')}_{datetime.now().year}"

    __table_args__ = (
        Index('idx_project_org', 'organization_id'),
        Index('idx_project_api_key', 'api_key'),
    )
