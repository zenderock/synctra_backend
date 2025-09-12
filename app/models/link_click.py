from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index, DECIMAL, func
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class LinkClick(BaseModel):
    __tablename__ = "link_clicks"
    
    link_id = Column(UUID(as_uuid=True), ForeignKey("dynamic_links.id"))
    
    ip_address = Column(INET)
    user_agent = Column(Text)
    referer = Column(Text)
    
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    
    platform = Column(String(50))
    device_type = Column(String(50))
    browser = Column(String(100))
    os = Column(String(100))
    
    converted = Column(Boolean, default=False)
    conversion_value = Column(DECIMAL(10, 2))
    
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    link = relationship("DynamicLink", back_populates="clicks")
    
    __table_args__ = (
        Index('idx_click_link', 'link_id'),
        Index('idx_click_date', 'clicked_at'),
        Index('idx_click_platform', 'platform'),
    )
