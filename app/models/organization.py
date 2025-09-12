from sqlalchemy import Column, String, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class Organization(BaseModel):
    __tablename__ = "organizations"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255))
    plan_type = Column(String(50), default='starter')
    settings = Column(JSON, default={})
    
    users = relationship("User", back_populates="organization")
    projects = relationship("Project", back_populates="organization")
    subscription = relationship("Subscription", back_populates="organization", uselist=False)
