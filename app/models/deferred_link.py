from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, func, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class DeferredLink(BaseModel):
    __tablename__ = "deferred_links"
    
    # Identifiants uniques
    device_id = Column(String(255), nullable=False)
    package_name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    
    # Données du lien original
    link_id = Column(String(36), nullable=False)
    original_url = Column(Text, nullable=False)
    parameters = Column(JSON, default={})
    
    # Métadonnées
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Statut
    is_consumed = Column(Boolean, default=False)
    consumed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_deferred_device_package', 'device_id', 'package_name', 'platform'),
        Index('idx_deferred_expires', 'expires_at'),
        Index('idx_deferred_consumed', 'is_consumed'),
    )
