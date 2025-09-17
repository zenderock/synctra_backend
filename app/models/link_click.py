from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class LinkClick(Base):
    __tablename__ = "link_clicks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    link_id = Column(UUID(as_uuid=True), ForeignKey("dynamic_links.id"), nullable=False)
    
    # Informations utilisateur
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String, nullable=True)
    referer = Column(String, nullable=True)
    
    # Géolocalisation
    country = Column(String(2), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Détection de plateforme
    platform = Column(String(50), nullable=True)  # android, ios, web, desktop
    device_type = Column(String(50), nullable=True)  # mobile, tablet, desktop
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    
    # Tracking de conversion
    converted = Column(Boolean, default=False)
    conversion_value = Column(DECIMAL(10,2), nullable=True)
    
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())

    link = relationship("DynamicLink", back_populates="clicks")

    __table_args__ = (
        Index('idx_click_link', 'link_id'),
        Index('idx_click_date', 'clicked_at'),
        Index('idx_click_platform', 'platform'),
    )
