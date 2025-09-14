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
    
    # Si c'est un appareil mobile, gérer la redirection intelligente côté serveur
    if user_agent.is_mobile:
        project = link.project
        
        # Générer l'URL de redirection basée sur la plateforme
        if user_agent.os.family == 'Android' and link.android_package:
            # Utiliser Intent URL pour Android (plus fiable)
            package_parts = link.android_package.split('.')
            app_name = package_parts[-1] if package_parts else "app"
            
            # Construire l'Intent URL avec fallback automatique
            fallback_url = link.android_fallback_url or str(link.original_url)
            intent_url = f"intent://open#Intent;scheme={app_name};package={link.android_package};S.browser_fallback_url={fallback_url};end"
            
            return RedirectResponse(url=intent_url, status_code=302)
            
        elif user_agent.os.family == 'iOS' and link.ios_bundle_id:
            # Pour iOS, essayer le custom scheme puis fallback
            bundle_parts = link.ios_bundle_id.split('.')
            app_name = bundle_parts[-1] if bundle_parts else "app"
            custom_scheme = f"{app_name}://open"
            
            # Créer une page de redirection simple pour iOS
            fallback_url = link.ios_fallback_url or str(link.original_url)
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Redirection...</title>
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                        background: #f5f5f7;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                        color: #1d1d1f;
                    }}
                    .container {{ 
                        text-align: center;
                        background: white;
                        padding: 2rem;
                        border-radius: 16px;
                        border: 1px solid #d2d2d7;
                    }}
                    .btn {{ 
                        background: #007aff;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-size: 16px;
                        margin: 8px;
                        cursor: pointer;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Ouverture de l'application</h2>
                    <p>Si l'application ne s'ouvre pas automatiquement :</p>
                    <button class="btn" onclick="window.location.href='{fallback_url}'">Continuer sur le web</button>
                </div>
                <script>
                    // Tentative d'ouverture immédiate
                    window.location.href = '{custom_scheme}';
                    
                    // Fallback après 3 secondes
                    setTimeout(() => {{
                        window.location.href = '{fallback_url}';
                    }}, 3000);
                </script>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
        
        else:
            # Mobile sans configuration app - redirection directe
            return RedirectResponse(url=str(link.original_url), status_code=302)
    
    # Redirection directe pour les autres cas (desktop)
    return RedirectResponse(url=str(link.original_url), status_code=302)
