from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
import ipaddress

from app.core.database import get_db, get_redis
from app.models.dynamic_link import DynamicLink
from app.models.link_click import LinkClick
from app.services.platform_detector import PlatformDetector
from app.services.deferred_deep_linking import deferred_service
from app.core.exceptions import NotFoundException

router = APIRouter()

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
    redis_client = get_redis()
    
    cache_key = f"link:{short_code}"
    cached_link = redis_client.get(cache_key)
    
    if cached_link:
        import json
        link_data = json.loads(cached_link)
    else:
        link = db.query(DynamicLink).filter(
            DynamicLink.short_code == short_code,
            DynamicLink.is_active == True
        ).first()
        
        if not link:
            raise NotFoundException("Lien non trouvé")
        
        if link.expires_at and link.expires_at < datetime.utcnow():
            raise NotFoundException("Lien expiré")
        
        link_data = {
            "id": str(link.id),
            "original_url": link.original_url,
            "android_package": link.android_package,
            "android_fallback_url": link.android_fallback_url,
            "ios_bundle_id": link.ios_bundle_id,
            "ios_fallback_url": link.ios_fallback_url,
            "desktop_fallback_url": link.desktop_fallback_url
        }
        
        redis_client.setex(cache_key, 3600, json.dumps(link_data))
    
    user_agent = request.headers.get("User-Agent", "")
    platform_info = PlatformDetector.detect_platform(user_agent)
    
    client_ip = get_client_ip(request)
    geo_info = get_geolocation_from_ip(client_ip)
    
    click = LinkClick(
        link_id=link_data["id"],
        ip_address=client_ip,
        user_agent=user_agent,
        referer=request.headers.get("Referer"),
        country=geo_info["country"],
        region=geo_info["region"],
        city=geo_info["city"],
        platform=platform_info["platform"],
        device_type=platform_info["device_type"],
        browser=platform_info["browser"],
        os=platform_info["os"]
    )
    
    db.add(click)
    db.commit()
    db.refresh(click)
    
    # Récupérer le lien complet pour le deferred deep linking
    full_link = db.query(DynamicLink).filter(DynamicLink.id == link_data["id"]).first()
    
    # Vérifier si l'app est installée
    platform = platform_info["platform"]
    is_mobile = platform in ["android", "ios"]
    
    if is_mobile:
        package_name = link_data.get("android_package") if platform == "android" else None
        bundle_id = link_data.get("ios_bundle_id") if platform == "ios" else None
        
        app_installed = deferred_service.is_app_installed(user_agent, package_name, bundle_id)
        
        if not app_installed and (package_name or bundle_id):
            # Créer un contexte de deferred deep linking
            tracking_id = deferred_service.create_deferred_context(full_link, click)
            
            # Retourner une page intermédiaire
            html_content = deferred_service.create_deferred_link_page(
                full_link, tracking_id, platform
            )
            return HTMLResponse(content=html_content)
    
    # Redirection normale si l'app est installée ou pas de mobile
    redirect_url = PlatformDetector.get_redirect_url(link_data, platform_info)
    return RedirectResponse(url=redirect_url, status_code=302)
