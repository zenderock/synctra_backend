from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationCategory(str, Enum):
    SYSTEM = "system"
    SECURITY = "security"
    ANALYTICS = "analytics"
    LINKS = "links"


class NotificationBase(BaseModel):
    type: NotificationType = NotificationType.INFO
    category: NotificationCategory = NotificationCategory.SYSTEM
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    action_url: Optional[str] = Field(None, max_length=500)


class NotificationCreate(NotificationBase):
    user_id: str


class NotificationUpdate(BaseModel):
    read: Optional[bool] = None
    read_at: Optional[datetime] = None


class NotificationInDBBase(NotificationBase):
    id: str
    user_id: str
    read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Notification(NotificationInDBBase):
    pass


class NotificationInDB(NotificationInDBBase):
    pass
