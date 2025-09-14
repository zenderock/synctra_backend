from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    custom_domain: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}
    
    # Configuration App Links / Universal Links
    android_package: Optional[str] = None
    ios_bundle_id: Optional[str] = None
    android_sha256_fingerprints: Optional[List[str]] = []
    ios_team_id: Optional[str] = None
    
    # Fichiers de vérification de domaine
    assetlinks_json: Optional[Dict[str, Any]] = None
    apple_app_site_association: Optional[Dict[str, Any]] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    custom_domain: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    
    # Configuration App Links / Universal Links
    android_package: Optional[str] = None
    ios_bundle_id: Optional[str] = None
    android_sha256_fingerprints: Optional[List[str]] = None
    ios_team_id: Optional[str] = None
    
    # Fichiers de vérification de domaine
    assetlinks_json: Optional[Dict[str, Any]] = None
    apple_app_site_association: Optional[Dict[str, Any]] = None

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
