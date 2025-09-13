from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Callable

from app.core.database import get_db
from app.services.subscription_service import SubscriptionService
from app.core.deps import get_current_active_user

class SubscriptionMiddleware:
    
    @staticmethod
    async def check_project_limit(request: Request, call_next: Callable):
        if request.method == "POST" and "/projects" in str(request.url):
            try:
                db: Session = next(get_db())
                
                # Récupérer l'utilisateur depuis le token
                authorization = request.headers.get("Authorization")
                if not authorization:
                    return await call_next(request)
                
                # Simuler la récupération de l'organisation (à adapter selon votre auth)
                # organization_id = get_organization_from_token(authorization)
                
                # Pour l'instant, on laisse passer et on vérifiera dans les endpoints
                return await call_next(request)
                
            except Exception:
                return await call_next(request)
        
        return await call_next(request)
    
    @staticmethod
    async def check_member_limit(request: Request, call_next: Callable):
        if request.method == "POST" and "/users" in str(request.url):
            try:
                db: Session = next(get_db())
                
                # Logique similaire pour vérifier les limites de membres
                return await call_next(request)
                
            except Exception:
                return await call_next(request)
        
        return await call_next(request)

def require_feature(feature_name: str):
    """Décorateur pour vérifier l'accès aux fonctionnalités premium"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Récupérer la session DB et l'organisation depuis les arguments
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if db and current_user and current_user.organization_id:
                has_access = SubscriptionService.has_feature_access(
                    db, 
                    str(current_user.organization_id), 
                    feature_name
                )
                
                if not has_access:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Cette fonctionnalité nécessite un plan supérieur. Fonctionnalité requise: {feature_name}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_limit_check(limit_type: str):
    """Décorateur pour vérifier les limites d'usage"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if db and current_user and current_user.organization_id:
                organization_id = str(current_user.organization_id)
                
                if limit_type == "projects":
                    if not SubscriptionService.check_project_limit(db, organization_id):
                        raise HTTPException(
                            status_code=403,
                            detail="Limite de projets atteinte pour votre plan actuel"
                        )
                
                elif limit_type == "members":
                    if not SubscriptionService.check_member_limit(db, organization_id):
                        raise HTTPException(
                            status_code=403,
                            detail="Limite de membres atteinte pour votre plan actuel"
                        )
                
                elif limit_type == "links":
                    project_id = kwargs.get('project_id')
                    if project_id and not SubscriptionService.check_links_limit(db, project_id):
                        raise HTTPException(
                            status_code=403,
                            detail="Limite de liens atteinte pour votre plan actuel"
                        )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
