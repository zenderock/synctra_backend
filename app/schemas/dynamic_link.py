from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class DynamicLinkBase(BaseModel):
    original_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    android_package: Optional[str] = None
    android_fallback_url: Optional[str] = None
    ios_bundle_id: Optional[str] = None
    ios_fallback_url: Optional[str] = None
    desktop_fallback_url: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    link_type: str = "standard"
    expires_at: Optional[datetime] = None


class DynamicLinkCreate(DynamicLinkBase):
    pass


class DynamicLinkUpdate(BaseModel):
    original_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    android_package: Optional[str] = None
    android_fallback_url: Optional[str] = None
    ios_bundle_id: Optional[str] = None
    ios_fallback_url: Optional[str] = None
    desktop_fallback_url: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    link_type: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class DynamicLinkInDBBase(DynamicLinkBase):
    id: uuid.UUID
    project_id: uuid.UUID
    short_code: str
    short_url: Optional[str] = None
    is_active: bool
    clicks: Optional[int] = 0
    conversions: Optional[int] = 0
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DynamicLink(DynamicLinkInDBBase):
    pass


class DynamicLinkInDB(DynamicLinkInDBBase):
    pass
