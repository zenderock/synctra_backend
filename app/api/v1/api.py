from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, organizations, projects, dynamic_links, redirect, analytics, referral_codes, notifications, sdk, invitations

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(dynamic_links.router, prefix="/projects", tags=["dynamic_links"])
api_router.include_router(analytics.router, prefix="/projects", tags=["analytics"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(referral_codes.router, tags=["referral_codes"])
api_router.include_router(invitations.router, prefix="/invitations", tags=["invitations"])
api_router.include_router(redirect.router, prefix="", tags=["redirect"])
api_router.include_router(sdk.router, prefix="", tags=["sdk"])
