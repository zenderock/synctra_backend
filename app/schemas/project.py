from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    custom_domain: Optional[str] = None
    status: str = "development"


class ProjectCreate(ProjectBase):
    settings: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    custom_domain: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    android_package: Optional[str] = None
    ios_bundle_id: Optional[str] = None
    app_url: Optional[str] = None
    android_fallback_url: Optional[str] = None
    ios_fallback_url: Optional[str] = None
    desktop_fallback_url: Optional[str] = None
    assetlinks_json: Optional[Dict[str, Any]] = None
    apple_app_site_association: Optional[Dict[str, Any]] = None


class ProjectAppConfigUpdate(BaseModel):
    android_package: Optional[str] = None
    ios_bundle_id: Optional[str] = None
    app_url: Optional[str] = None
    android_fallback_url: Optional[str] = None
    ios_fallback_url: Optional[str] = None
    desktop_fallback_url: Optional[str] = None


class ProjectInDBBase(ProjectBase):
    id: uuid.UUID
    project_id: str
    organization_id: uuid.UUID
    api_key: str
    settings: Dict[str, Any]
    android_package: Optional[str] = None
    ios_bundle_id: Optional[str] = None
    app_url: Optional[str] = None
    android_fallback_url: Optional[str] = None
    ios_fallback_url: Optional[str] = None
    desktop_fallback_url: Optional[str] = None
    assetlinks_json: Optional[Dict[str, Any]] = None
    apple_app_site_association: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Project(ProjectInDBBase):
    pass


class ProjectInDB(ProjectInDBBase):
    pass
