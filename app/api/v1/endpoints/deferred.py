from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.services.deferred_deep_linking import deferred_service
from app.services.platform_detector import PlatformDetector
from app.models.link_click import LinkClick

router = APIRouter()

class DeferredContextRequest(BaseModel):
    tracking_id: str
    app_identifier: Optional[str] = None
    device_info: Optional[dict] = None

class TrackingRequest(BaseModel):
    tracking_id: str

@router.get("/context/{tracking_id}")
async def get_deferred_context(
    tracking_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère le contexte de deep linking différé après installation de l'app
    """
    context = deferred_service.get_deferred_context(tracking_id)
    if not context:
        raise HTTPException(status_code=404, detail="Contexte de tracking non trouvé")
    
    return {
        "success": True,
        "context": context
    }

@router.post("/app-opened")
async def handle_app_opened(
    request_data: DeferredContextRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint appelé par l'app mobile après installation pour récupérer le contexte
    """
    result = deferred_service.handle_app_open(
        request_data.tracking_id,
        request_data.app_identifier or "unknown",
        db
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Contexte de tracking non trouvé")
    
    return result

@router.post("/track-web-continue")
async def track_web_continue(
    request_data: TrackingRequest,
    db: Session = Depends(get_db)
):
    """
    Track quand l'utilisateur choisit de continuer sur le web
    """
    context = deferred_service.get_deferred_context(request_data.tracking_id)
    if context:
        click_id = context.get("click_id")
        if click_id:
            click = db.query(LinkClick).filter(LinkClick.id == click_id).first()
            if click:
                # Marquer comme "web continue" dans les analytics
                click.converted = False  # Pas une vraie conversion app
                db.commit()
    
    return {"success": True}

@router.get("/install-status/{tracking_id}")
async def check_install_status(
    tracking_id: str,
    request: Request
):
    """
    Vérifie si l'app a été installée (polling depuis la page d'attente)
    """
    context = deferred_service.get_deferred_context(tracking_id)
    if not context:
        return {"installed": False, "expired": True}
    
    # Logique simple - dans un vrai système, on pourrait avoir des mécaniques plus sophistiquées
    user_agent = request.headers.get("User-Agent", "")
    
    # Vérifier si l'User-Agent a changé (signe possible d'installation)
    original_platform = context.get("platform")
    current_platform_info = PlatformDetector.detect_platform(user_agent)
    
    return {
        "installed": False,  # À implémenter selon vos besoins
        "expired": False,
        "context": context
    }
