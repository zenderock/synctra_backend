from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class AnalyticsOverview(BaseModel):
    total_clicks: int
    total_links: int
    conversion_rate: float
    top_countries: List[Dict[str, Any]]
    top_platforms: List[Dict[str, Any]]
    clicks_over_time: List[Dict[str, Any]]

class LinkAnalytics(BaseModel):
    link_id: str
    short_code: str
    title: Optional[str]
    total_clicks: int
    unique_clicks: int
    conversion_rate: float
    top_countries: List[Dict[str, Any]]
    top_platforms: List[Dict[str, Any]]
    clicks_by_day: List[Dict[str, Any]]

class ClickEvent(BaseModel):
    id: str
    link_id: str
    ip_address: Optional[str]
    country: Optional[str]
    region: Optional[str]
    city: Optional[str]
    platform: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    converted: bool
    conversion_value: Optional[float]
    clicked_at: datetime
    
    class Config:
        from_attributes = True

class ExportRequest(BaseModel):
    format: str = "csv"
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    link_ids: Optional[List[str]] = None
