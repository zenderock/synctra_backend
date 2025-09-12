from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    custom_domain: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    custom_domain: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class ProjectResponse(ProjectBase):
    id: str
    project_id: str
    api_key: str
    organization_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
