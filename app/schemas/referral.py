from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReferralCodeBase(BaseModel):
    code: str
    reward_type: str
    reward_value: float
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None

class ReferralCodeCreate(ReferralCodeBase):
    pass

class ReferralCodeUpdate(BaseModel):
    reward_type: Optional[str] = None
    reward_value: Optional[float] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None

class ReferralCodeResponse(ReferralCodeBase):
    id: str
    project_id: str
    user_id: str
    current_uses: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReferralUse(BaseModel):
    code: str
    user_identifier: Optional[str] = None
