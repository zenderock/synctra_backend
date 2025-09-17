from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class InvitationBase(BaseModel):
    email: EmailStr
    role: str = 'member'


class InvitationCreate(InvitationBase):
    pass


class InvitationUpdate(BaseModel):
    status: Optional[str] = None
    token: Optional[str] = None
    accepted_at: Optional[datetime] = None
    accepted_by_id: Optional[str] = None
    invited_at: Optional[datetime] = None


class Invitation(InvitationBase):
    id: str
    token: str
    status: str
    organization_id: str
    invited_by_id: str
    accepted_by_id: Optional[str] = None
    invited_at: datetime
    accepted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def model_validate(cls, obj, **kwargs):
        if hasattr(obj, '__dict__'):
            return cls(
                id=str(obj.id),
                email=obj.email,
                role=obj.role,
                token=obj.token,
                status=obj.status,
                organization_id=str(obj.organization_id),
                invited_by_id=str(obj.invited_by_id),
                accepted_by_id=str(obj.accepted_by_id) if obj.accepted_by_id else None,
                invited_at=obj.invited_at,
                accepted_at=obj.accepted_at,
                expires_at=obj.expires_at
            )
        return super().model_validate(obj, **kwargs)


class UserCreateFromInvitation(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
