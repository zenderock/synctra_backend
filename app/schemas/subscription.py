from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.subscription_plans import PlanType

class SubscriptionBase(BaseModel):
    plan_type: PlanType
    status: str = "active"
    amount: float = 0
    currency: str = "EUR"
    billing_interval: str = "monthly"

class SubscriptionCreate(SubscriptionBase):
    organization_id: str
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None

class SubscriptionUpdate(BaseModel):
    plan_type: Optional[PlanType] = None
    status: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None

class SubscriptionResponse(SubscriptionBase):
    id: str
    organization_id: str
    stripe_subscription_id: Optional[str]
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    is_trial: bool
    trial_end: Optional[datetime]
    projects_used: int
    members_used: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlanLimitsResponse(BaseModel):
    max_projects: Optional[int]
    max_organization_members: int
    has_full_analytics: bool
    has_custom_domain: bool
    has_ip_restrictions: bool
    max_links_per_project: Optional[int]

class PlanFeaturesResponse(BaseModel):
    name: str
    price: float
    currency: str
    billing_period: str
    features: list[str]

class UsageStatsResponse(BaseModel):
    plan_type: str
    projects: Dict[str, Any]
    members: Dict[str, Any]
    links: Dict[str, Any]
    features: Dict[str, bool]

class UpgradeRequest(BaseModel):
    new_plan: PlanType
    stripe_payment_method_id: Optional[str] = None
