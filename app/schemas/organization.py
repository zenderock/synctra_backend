from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class OrganizationBase(BaseModel):
    name: str
    slug: Optional[str] = None
    domain: Optional[str] = None
    plan_type: str = "free"


class OrganizationCreate(OrganizationBase):
    name: str  # Rendre explicite que name est requis


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    plan_type: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationInDBBase(OrganizationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any]

    class Config:
        from_attributes = True


class Organization(OrganizationInDBBase):
    pass


class OrganizationInDB(OrganizationInDBBase):
    pass
