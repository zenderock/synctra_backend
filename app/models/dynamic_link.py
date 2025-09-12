from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class DynamicLink(BaseModel):
    __tablename__ = "dynamic_links"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    short_code = Column(String(20), unique=True, nullable=False, index=True)
    original_url = Column(Text, nullable=False)
    title = Column(String(255))
    description = Column(Text)
    
    android_package = Column(String(255))
    android_fallback_url = Column(Text)
    ios_bundle_id = Column(String(255))
    ios_fallback_url = Column(Text)
    desktop_fallback_url = Column(Text)
    
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    utm_term = Column(String(100))
    utm_content = Column(String(100))
    
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    project = relationship("Project", back_populates="dynamic_links")
    created_by_user = relationship("User", back_populates="created_links")
    clicks = relationship("LinkClick", back_populates="link")
    
    __table_args__ = (
        Index('idx_link_project', 'project_id'),
        Index('idx_link_short_code', 'short_code'),
        Index('idx_link_created_by', 'created_by'),
    )
