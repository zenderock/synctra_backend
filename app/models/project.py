from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class Project(BaseModel):
    __tablename__ = "projects"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    domain = Column(String(255))
    is_active = Column(Boolean, default=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    custom_domain = Column(String(255))
    status = Column(String(50), default='development')
    settings = Column(JSON, default={})
    
    organization = relationship("Organization", back_populates="projects")
    dynamic_links = relationship("DynamicLink", back_populates="project")
    referral_codes = relationship("ReferralCode", back_populates="project")
    
    __table_args__ = (
        Index('idx_project_org', 'organization_id'),
        Index('idx_project_api_key', 'api_key'),
    )
