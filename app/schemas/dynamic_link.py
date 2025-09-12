from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class DynamicLinkBase(BaseModel):
    original_url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None
    android_package: Optional[str] = None
    android_fallback_url: Optional[HttpUrl] = None
    ios_bundle_id: Optional[str] = None
    ios_fallback_url: Optional[HttpUrl] = None
    desktop_fallback_url: Optional[HttpUrl] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    expires_at: Optional[datetime] = None

class DynamicLinkCreate(DynamicLinkBase):
    pass

class DynamicLinkUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    title: Optional[str] = None
    description: Optional[str] = None
    android_package: Optional[str] = None
    android_fallback_url: Optional[HttpUrl] = None
    ios_bundle_id: Optional[str] = None
    ios_fallback_url: Optional[HttpUrl] = None
    desktop_fallback_url: Optional[HttpUrl] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None

class DynamicLinkResponse(DynamicLinkBase):
    id: str
    project_id: str
    short_code: str
    short_url: str
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
