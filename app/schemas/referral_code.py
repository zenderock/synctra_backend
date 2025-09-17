from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal
import uuid


class ReferralCodeBase(BaseModel):
    code: str
    reward_type: str
    reward_value: Optional[Decimal] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class ReferralCodeCreate(ReferralCodeBase):
    project_id: Optional[str] = None
    user_id: Optional[str] = None


class ReferralCodeUpdate(BaseModel):
    reward_type: Optional[str] = None
    reward_value: Optional[Decimal] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class ReferralCodeInDBBase(ReferralCodeBase):
    id: str
    project_id: str
    user_id: str
    current_uses: int
    created_at: datetime

    @field_validator('id', 'project_id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class ReferralCode(ReferralCodeInDBBase):
    pass


class ReferralCodeInDB(ReferralCodeInDBBase):
    pass
