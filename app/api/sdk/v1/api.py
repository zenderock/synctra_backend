from fastapi import APIRouter

from app.api.sdk.v1.endpoints import links, analytics, referrals, apps, deferred_links

api_router = APIRouter()

api_router.include_router(links.router, prefix="/links", tags=["SDK Links"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["SDK Analytics"])
api_router.include_router(referrals.router, prefix="/referrals", tags=["SDK Referrals"])
api_router.include_router(apps.router, prefix="/apps", tags=["SDK Apps"])
api_router.include_router(deferred_links.router, prefix="/deferred-links", tags=["SDK Deferred Links"])
