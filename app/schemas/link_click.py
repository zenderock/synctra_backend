from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class LinkClickBase(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referer: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    platform: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    converted: bool = False
    conversion_value: Optional[float] = None


class LinkClickCreate(LinkClickBase):
    pass


class LinkClickUpdate(BaseModel):
    converted: Optional[bool] = None
    conversion_value: Optional[float] = None


class LinkClickInDBBase(LinkClickBase):
    id: uuid.UUID
    link_id: uuid.UUID
    clicked_at: datetime

    class Config:
        from_attributes = True


class LinkClick(LinkClickInDBBase):
    pass


class LinkClickInDB(LinkClickInDBBase):
    pass
