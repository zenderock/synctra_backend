from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    avatar_url = Column(String(500))
    organization_id = Column(String(36), ForeignKey("organizations.id"))
    role = Column(String(50), default='member')
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    
    organization = relationship("Organization", back_populates="users")
    created_links = relationship("DynamicLink", back_populates="created_by_user")
    referral_codes = relationship("ReferralCode", back_populates="user")
