from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
import httpx

from app import crud, models
from app.api import deps
from app.utils.platform_detection import detect_platform_from_user_agent, get_fallback_url
from app.models.link_click import LinkClick
from app.models.referral_code import ReferralCode

router = APIRouter()


@router.get("/r/{short_code}")
async def redirect_link(
    *,
    short_code: str,
    request: Request,
    db: Session = Depends(deps.get_db)
) -> Any:
    # D'abord chercher dans les liens dynamiques
    link = crud.dynamic_link.get_by_short_code(db, short_code=short_code)
    
    # Si pas trouvé dans les liens, chercher dans les codes de parrainage simples
    if not link:
        referral_code = db.query(ReferralCode).filter(
            ReferralCode.code == short_code,
            ReferralCode.is_active == True
        ).first()
        
        if referral_code:
            return handle_referral_code_redirect(referral_code, request, db)
    
    if not link or not link.is_active:
        raise HTTPException(status_code=404, detail="Lien non trouvé ou inactif")
    
    # Vérifier si le lien a expiré
    from datetime import datetime
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Lien expiré")
    
    # Récupérer les informations de la requête
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host
    referer = request.headers.get("referer", "")
    
    # Détection de plateforme
    platform_info = detect_platform_from_user_agent(user_agent)
    
    # Géolocalisation (optionnelle - nécessite une base de données GeoIP)
    country = None
    region = None
    city = None
    
    # Enregistrer le clic
    click = LinkClick(
        link_id=link.id,
        ip_address=ip_address,
        user_agent=user_agent,
        referer=referer,
        country=country,
        region=region,
        city=city,
        platform=platform_info["platform"],
        device_type=platform_info["device_type"],
        browser=platform_info["browser"],
        os=platform_info["os"]
    )
    db.add(click)
    db.commit()
    
    # Vérifier si on doit utiliser la détection d'app native
    if (link.android_package or link.ios_bundle_id) and platform_info["device_type"] == "mobile":
        return generate_app_detection_page(link, platform_info)
    
    # Déterminer l'URL de redirection classique
    redirect_url = link.original_url
    
    # Vérifier s'il faut rediriger vers une URL spécifique selon la plateforme
    fallback_url = get_fallback_url(
        user_agent,
        link.android_fallback_url,
        link.ios_fallback_url,
        link.desktop_fallback_url
    )
    
    if fallback_url:
        redirect_url = fallback_url
    
    # Ajouter les paramètres UTM si définis
    if any([link.utm_source, link.utm_medium, link.utm_campaign, link.utm_term, link.utm_content]):
        separator = "&" if "?" in redirect_url else "?"
        utm_params = []
        
        if link.utm_source:
            utm_params.append(f"utm_source={link.utm_source}")
        if link.utm_medium:
            utm_params.append(f"utm_medium={link.utm_medium}")
        if link.utm_campaign:
            utm_params.append(f"utm_campaign={link.utm_campaign}")
        if link.utm_term:
            utm_params.append(f"utm_term={link.utm_term}")
        if link.utm_content:
            utm_params.append(f"utm_content={link.utm_content}")
        
        if utm_params:
            redirect_url += separator + "&".join(utm_params)
    
    return RedirectResponse(url=redirect_url, status_code=302)


def handle_referral_code_redirect(referral_code, request, db):
    """
    Gère la redirection pour un code de parrainage simple
    """
    # Récupérer les informations de la requête
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host
    referer = request.headers.get("referer", "")
    
    # Détection de plateforme
    platform_info = detect_platform_from_user_agent(user_agent)
    
    # Vérifier si on doit utiliser la détection d'app native pour les codes de parrainage
    if platform_info["device_type"] == "mobile":
        return generate_app_detection_page(None, platform_info, referral_code=referral_code)
    
    # Pour les autres cas, rediriger vers une page par défaut ou une URL configurée
    redirect_url = "https://votre-site.com/parrainage"  # URL par défaut
    
    return RedirectResponse(url=redirect_url, status_code=302)




def generate_app_detection_page(link, platform_info, referral_code=None):
    """
    Génère une page HTML avec JavaScript pour détecter et ouvrir l'app native
    """
    # Récupérer le projet pour les informations globales
    if referral_code:
        project = referral_code.project
    else:
        project = link.project
    
    # Construire l'URL scheme basée sur le package/bundle du projet
    app_scheme = ""
    store_url = ""
    
    if referral_code:
        # Cas code de parrainage simple
        if platform_info["platform"] == "android" and project.android_package:
            app_scheme = f"synctra://open?rel={referral_code.code}"
            store_url = project.android_fallback_url or f"https://play.google.com/store/apps/details?id={project.android_package}"
        elif platform_info["platform"] == "ios" and project.ios_bundle_id:
            app_scheme = f"synctra://open?rel={referral_code.code}"
            store_url = project.ios_fallback_url or f"https://apps.apple.com/app/id{project.ios_bundle_id}"
        fallback_url = project.app_url or project.desktop_fallback_url or "https://votre-site.com"
    else:
        # Cas lien dynamique - utiliser les infos du projet
        if platform_info["platform"] == "android" and project.android_package:
            app_scheme = f"synctra://open?id={link.id}"
            store_url = project.android_fallback_url or f"https://play.google.com/store/apps/details?id={project.android_package}"
        elif platform_info["platform"] == "ios" and project.ios_bundle_id:
            app_scheme = f"synctra://open?id={link.id}"
            store_url = project.ios_fallback_url or f"https://apps.apple.com/app/id{project.ios_bundle_id}"
        fallback_url = link.original_url
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Redirection...</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #ffffff;
                color: #1a1a1a;
                line-height: 1.5;
            }}
            .container {{
                text-align: center;
                padding: 2rem;
                max-width: 400px;
            }}
            .spinner {{
                width: 32px;
                height: 32px;
                border: 2px solid #f0f0f0;
                border-top: 2px solid #007aff;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
                margin: 0 auto 1.5rem;
            }}
            h2 {{
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #1a1a1a;
            }}
            p {{
                font-size: 0.95rem;
                color: #666666;
                font-weight: 400;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            @media (prefers-color-scheme: dark) {{
                body {{
                    background-color: #000000;
                    color: #ffffff;
                }}
                h2 {{
                    color: #ffffff;
                }}
                p {{
                    color: #999999;
                }}
                .spinner {{
                    border-color: #333333;
                    border-top-color: #007aff;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h2>Ouverture de l'application...</h2>
            <p>Si l'application ne s'ouvre pas automatiquement, vous serez redirigé.</p>
        </div>

       <script src="https://cdn.jsdelivr.net/npm/open-native-app@0.3.3/assets/index.min.js"></script>
        <script>
            // Configuration des URLs
            const appScheme = '{app_scheme}';
            const storeUrl = '{store_url}';
            const fallbackUrl = '{fallback_url}';
            
            // Fonction de redirection vers le store ou fallback
            function redirectToStore() {{
                console.log('Tentative d\\'enregistrement signature...');
                
                // Enregistrer la signature d'app non installée (seulement pour les liens dynamiques)
                const linkId = '{link.id if link else ""}';
                if (linkId) {{
                    fetch('/api/v1/r/' + linkId + '/app-not-installed', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            platform: '{platform_info["platform"]}',
                            user_agent: navigator.userAgent,
                            timestamp: new Date().toISOString()
                        }})
                    }})
                .then(response => {{
                    console.log('Signature enregistrée:', response.status);
                    alert(response.status);
                    // Redirection après l'enregistrement
                    if (storeUrl) {{
                        window.location.href = storeUrl;
                    }} else {{
                        window.location.href = fallbackUrl;
                    }}
                }})
                }} else {{
                    // Pour les codes de parrainage, redirection directe
                    if (storeUrl) {{
                        window.location.href = storeUrl;
                    }} else {{
                        window.location.href = fallbackUrl;
                    }}
                }}
                .catch(err => {{
                    console.log('Erreur enregistrement signature:', err);
                    // Redirection même en cas d'erreur
                    if (storeUrl) {{
                        window.location.href = storeUrl;
                    }} else {{
                        window.location.href = fallbackUrl;
                    }}
                }});
            }}
            
            // Tentative d'ouverture de l'app native
            if (appScheme && typeof openApp !== 'undefined') {{
                console.log('Tentative d\\'ouverture app:', appScheme);
                openApp.open(
                    appScheme,
                    function(code) {{
                        // Callback de succès - l'app s'est ouverte
                        console.log('App ouverte avec succès:', code);
                    }},
                    function() {{
                        // Callback d'erreur - app non installée ou échec
                        console.log('App non installée ou erreur, redirection vers le store');
                        redirectToStore();
                    }},
                    2000 // Timeout de 2 secondes
                );
            }} else {{
                // Fallback si open-native-app n'est pas disponible
                console.log('openApp non disponible, redirection directe');
                setTimeout(redirectToStore, 1000);
            }}
            
            // Fallback de sécurité après 5 secondes (augmenté pour laisser le temps au fetch)
            setTimeout(function() {{
                if (document.visibilityState === 'visible') {{
                    console.log('Fallback de sécurité activé');
                    redirectToStore();
                }}
            }}, 5000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)


@router.post("/r/{link_id}/app-not-installed")
async def record_app_not_installed(
    *,
    link_id: str,
    request: Request,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Enregistre la signature quand l'app n'est pas installée
    """
    try:
        # Récupérer les données du body
        body = await request.json()
        
        # Récupérer les informations de la requête
        ip_address = request.client.host
        user_agent = body.get("user_agent", request.headers.get("user-agent", ""))
        platform = body.get("platform", "unknown")
        timestamp = body.get("timestamp")
        
        # Créer un enregistrement de signature d'app non installée
        app_not_installed_record = {
            "link_id": link_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "platform": platform,
            "timestamp": timestamp,
            "event_type": "app_not_installed"
        }
        
        # Ici vous pouvez créer un modèle AppInstallSignature ou l'ajouter à LinkClick
        # Pour l'instant, on utilise LinkClick avec un champ event_type
        click = LinkClick(
            link_id=link_id,
            ip_address=ip_address,
            user_agent=user_agent,
            platform=platform,
            device_type="mobile",
            browser="app_detection",
            os=platform
        )
        db.add(click)
        db.commit()
        
        return {"status": "success", "message": "Signature enregistrée"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
