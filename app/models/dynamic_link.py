from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import secrets
import string

from app.db.database import Base


class DynamicLink(Base):
    __tablename__ = "dynamic_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    short_code = Column(String(20), unique=True, nullable=False)
    original_url = Column(Text, nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Configuration deeplink
    android_package = Column(String(255), nullable=True)
    android_fallback_url = Column(Text, nullable=True)
    ios_bundle_id = Column(String(255), nullable=True)
    ios_fallback_url = Column(Text, nullable=True)
    desktop_fallback_url = Column(Text, nullable=True)
    
    # Paramètres UTM
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    utm_term = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)
    
    # Type de lien (parrainage)
    link_type = Column(String(50), default='standard')
    
    # Métadonnées
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="dynamic_links")
    created_by_user = relationship("User", back_populates="created_links")
    clicks = relationship("LinkClick", back_populates="link")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.short_code:
            self.short_code = self._generate_short_code()

    def _generate_short_code(self) -> str:
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(8))

    __table_args__ = (
        Index('idx_link_project', 'project_id'),
        Index('idx_link_short_code', 'short_code'),
        Index('idx_link_created_by', 'created_by'),
    )
