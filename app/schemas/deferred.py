from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DeferredContext(BaseModel):
    link_id: str
    short_code: str
    original_url: str
    click_id: str
    platform: str
    device_type: str
    country: Optional[str]
    utm_params: Dict[str, Optional[str]]
    created_at: str

class AppOpenRequest(BaseModel):
    tracking_id: str
    app_identifier: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None

class DeferredLinkResponse(BaseModel):
    success: bool
    original_url: str
    utm_params: Dict[str, Optional[str]]
    link_data: Dict[str, str]

class InstallStatusResponse(BaseModel):
    installed: bool
    expired: bool
    context: Optional[DeferredContext] = None
