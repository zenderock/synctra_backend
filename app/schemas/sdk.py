from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Modèles de base pour le SDK

class DeepLinkBase(BaseModel):
    originalUrl: str = Field(..., description="URL originale du lien")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Paramètres du lien")
    fallbackUrl: Optional[str] = Field(None, description="URL de fallback")
    iosAppStoreUrl: Optional[str] = Field(None, description="URL App Store iOS")
    androidPlayStoreUrl: Optional[str] = Field(None, description="URL Play Store Android")
    expiresAt: Optional[datetime] = Field(None, description="Date d'expiration")
    campaignId: Optional[str] = Field(None, description="ID de campagne")
    referralCode: Optional[str] = Field(None, description="Code de parrainage")

class DeepLinkCreate(DeepLinkBase):
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées du lien")

class DeepLinkUpdate(BaseModel):
    originalUrl: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    fallbackUrl: Optional[str] = None
    iosAppStoreUrl: Optional[str] = None
    androidPlayStoreUrl: Optional[str] = None
    expiresAt: Optional[datetime] = None
    isActive: Optional[bool] = None
    campaignId: Optional[str] = None
    referralCode: Optional[str] = None

class DeepLinkResponse(DeepLinkBase):
    id: str
    shortUrl: str
    createdAt: datetime
    isActive: bool

class AnalyticsEvent(BaseModel):
    type: str = Field(..., description="Type d'événement")
    linkId: str = Field(..., description="ID du lien")
    timestamp: datetime = Field(..., description="Timestamp de l'événement")
    properties: Dict[str, Any] = Field(default_factory=dict)
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    deviceId: Optional[str] = None
    platform: Optional[str] = None
    appVersion: Optional[str] = None
    userAgent: Optional[str] = None
    ipAddress: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    referrer: Optional[str] = None

class AnalyticsEventBatch(BaseModel):
    events: List[AnalyticsEvent]

class ReferralCodeBase(BaseModel):
    userId: str = Field(..., description="ID de l'utilisateur")
    code: Optional[str] = Field(None, description="Code personnalisé (généré si non fourni)")
    campaignId: Optional[str] = Field(None, description="ID de campagne")
    expiresAt: Optional[datetime] = Field(None, description="Date d'expiration")
    maxUses: int = Field(default=1, description="Nombre maximum d'utilisations")
    rewardAmount: Optional[float] = Field(None, description="Montant de la récompense")
    rewardType: Optional[str] = Field(None, description="Type de récompense")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReferralCodeCreate(ReferralCodeBase):
    pass

class ReferralCodeUpdate(BaseModel):
    expiresAt: Optional[datetime] = None
    maxUses: Optional[int] = None
    isActive: Optional[bool] = None
    rewardAmount: Optional[float] = None
    rewardType: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ReferralCodeResponse(ReferralCodeBase):
    createdAt: datetime
    currentUses: int
    isActive: bool

class ReferralCodeUse(BaseModel):
    userId: str
    timestamp: datetime

class AppInstallInfo(BaseModel):
    packageName: str
    status: str = Field(..., description="unknown|installed|notInstalled|checking")
    version: Optional[str] = None
    installedAt: Optional[datetime] = None
    checkedAt: datetime
    platform: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DeferredLinkCreate(BaseModel):
    linkId: str
    packageName: str
    deviceId: str
    timestamp: datetime
    parameters: Dict[str, Any] = Field(default_factory=dict)

class DeferredLinkQuery(BaseModel):
    packageName: str
    deviceId: str
    platform: str

# Réponses standardisées pour le SDK
class SDKResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    links: List[DeepLinkResponse]
    total: int
    limit: int
    offset: int

class AnalyticsResponse(BaseModel):
    totalClicks: int
    uniqueClicks: int
    conversions: int
    platforms: Dict[str, int]
    countries: Dict[str, int]
    timeline: List[Dict[str, Any]]

class ReferralAnalyticsResponse(BaseModel):
    totalUses: int
    uniqueUsers: int
    conversions: int
    revenue: float
    timeline: List[Dict[str, Any]]

class InstallAnalyticsResponse(BaseModel):
    totalInstalls: int
    platforms: Dict[str, int]
    timeline: List[Dict[str, Any]]
    conversionRate: float
