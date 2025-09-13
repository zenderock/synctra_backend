from fastapi import APIRouter

from app.api.v1.endpoints import auth, projects, links, analytics, referrals, deferred, subscriptions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentification"])
api_router.include_router(projects.router, prefix="/projects", tags=["projets"])
api_router.include_router(links.router, prefix="/projects/{project_id}/links", tags=["liens-dynamiques"])
api_router.include_router(analytics.router, prefix="/projects/{project_id}/analytics", tags=["analytics"])
api_router.include_router(referrals.router, prefix="/projects/{project_id}/referrals", tags=["parrainage"])
api_router.include_router(deferred.router, prefix="/deferred", tags=["deferred-deep-linking"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["abonnements"])
