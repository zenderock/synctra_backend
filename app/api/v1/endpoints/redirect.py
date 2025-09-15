from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import user_agents

from app.core.database import get_db
from app.models.dynamic_link import DynamicLink
from app.services.analytics_service import AnalyticsService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def get_geolocation_from_ip(ip: str) -> dict:
    try:
        return {"country": "FR", "region": "Île-de-France", "city": "Paris"}
    except:
        return {"country": None, "region": None, "city": None}

@router.get("/{short_code}")
async def redirect_link(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Rediriger vers l'URL cible ou afficher la page de redirection intelligente."""
    
    # Éviter les requêtes pour les fichiers système
    if short_code in ["favicon.ico", "robots.txt", "sitemap.xml", "docs", "redoc", "openapi.json"]:
        raise HTTPException(status_code=404, detail="Ressource non trouvée")
    
    # Récupérer le lien
    link = db.query(DynamicLink).filter(
        DynamicLink.short_code == short_code,
        DynamicLink.is_active == True
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    # Vérifier l'expiration
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Lien expiré")
    
    # Analyser l'user agent
    user_agent = user_agents.parse(str(request.headers.get("user-agent", "")))
    
    # Enregistrer l'analytics
    client_ip = get_client_ip(request)
    geo_info = get_geolocation_from_ip(client_ip)
    
    await AnalyticsService.record_click(
        db=db,
        link_id=link.id,
        ip_address=client_ip,
        user_agent=str(request.headers.get("user-agent", "")),
        referer=request.headers.get("referer"),
        country=geo_info["country"],
        device_type=user_agent.device.family,
        os=user_agent.os.family,
        browser=user_agent.browser.family
    )
    
    # Si c'est un appareil mobile, utiliser le template avec JS amélioré
    if user_agent.is_mobile and (link.android_package or link.ios_bundle_id):
        project = link.project
        
        # Préparer les données pour le template
        package_parts = (link.android_package or link.ios_bundle_id or "").split('.')
        app_name = package_parts[-1] if package_parts else "app"
        custom_scheme = f"{app_name}://"
        
        fallback_url = (
            link.android_fallback_url if user_agent.os.family == 'Android' 
            else link.ios_fallback_url if user_agent.os.family == 'iOS'
            else str(link.original_url)
        ) or str(link.original_url)
        
        # Utiliser le template avec le JS amélioré
        return templates.TemplateResponse("redirect.html", {
            "request": request,
            "custom_scheme": custom_scheme,
            "android_package": link.android_package or "",
            "ios_app_id": project.ios_bundle_id or "",  # Utiliser ios_bundle_id du projet
            "fallback_url": fallback_url,
            "android_fallback_url": link.android_fallback_url or "",
            "ios_fallback_url": link.ios_fallback_url or "",
            "original_url": str(link.original_url),
            "api_key": project.api_key,
            "project_id": project.id,
            "link_id": str(link.id),
            "assetlinks_json": project.assetlinks_json,
            "apple_app_site_association": project.apple_app_site_association,
            "has_assetlinks": "true" if project.assetlinks_json else "false",
            "has_apple_association": "true" if project.apple_app_site_association else "false",
            "utm_source": link.utm_source or "",
            "utm_medium": link.utm_medium or "",
            "utm_campaign": link.utm_campaign or "",
            "utm_content": link.utm_content or "",
            "utm_term": link.utm_term or ""
        })
    
    elif user_agent.is_mobile:
        # Mobile sans configuration app - redirection directe
        return RedirectResponse(url=str(link.original_url), status_code=302)
    
    # Redirection directe pour les autres cas (desktop)
    return RedirectResponse(url=str(link.original_url), status_code=302)
