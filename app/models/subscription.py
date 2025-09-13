from sqlalchemy import Column, String, Float, DateTime, ForeignKey, DECIMAL, Boolean, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.core.subscription_plans import PlanType

class Subscription(BaseModel):
    __tablename__ = "subscriptions"
    
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, unique=True)
    plan_type = Column(String(50), default=PlanType.STARTER.value)
    status = Column(String(50), default='active')  # active, cancelled, expired, suspended
    
    # Facturation
    stripe_subscription_id = Column(String(255), unique=True)
    stripe_customer_id = Column(String(255))
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    
    # Pricing
    amount = Column(DECIMAL(10, 2), default=0)
    currency = Column(String(3), default='EUR')
    billing_interval = Column(String(20), default='monthly')  # monthly, yearly
    
    # Trial
    trial_start = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))
    is_trial = Column(Boolean, default=False)
    
    # Usage tracking
    projects_used = Column(Integer, default=0)
    members_used = Column(Integer, default=1)  # Le créateur compte
    
    organization = relationship("Organization", back_populates="subscription")
