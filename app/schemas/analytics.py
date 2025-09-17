from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class LinkAnalytics(BaseModel):
    total_clicks: int
    unique_clicks: int
    conversion_rate: float
    top_countries: List[Dict[str, Any]]
    top_referrers: List[Dict[str, Any]]
    click_history: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class ProjectAnalytics(BaseModel):
    total_links: int
    total_clicks: int
    active_links: int
    conversion_rate: float
    top_links: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True
