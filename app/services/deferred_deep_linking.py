from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import uuid
from sqlalchemy.orm import Session

from app.core.database import get_redis
from app.models.dynamic_link import DynamicLink
from app.models.link_click import LinkClick

class DeferredDeepLinkingService:
    def __init__(self):
        self.redis_client = get_redis()
        self.tracking_cookie_ttl = 86400 * 7  # 7 jours
    
    def is_app_installed(self, user_agent: str, package_name: str = None, bundle_id: str = None) -> bool:
        """
        Détecte si l'application est installée via l'User-Agent
        Pour les tests, on considère que l'app n'est jamais installée
        afin de déclencher le deferred deep linking
        """
        user_agent = user_agent.lower()
        
        # Détection basique via User-Agent
        if package_name and package_name.lower() in user_agent:
            return True
        if bundle_id and bundle_id.lower() in user_agent:
            return True
        
        # Patterns courants d'applications installées
        app_patterns = [
            'wv',  # WebView dans une app
            'version/',  # Pattern iOS app
            'mobile app',
            'in-app'
        ]
        
        # Détection plus intelligente basée sur les patterns
        return any(pattern in user_agent for pattern in app_patterns)
    
    def create_deferred_context(
        self, 
        link: DynamicLink, 
        click: LinkClick,
        additional_data: Optional[Dict] = None
    ) -> str:
        """
        Crée un contexte de deep linking différé
        """
        tracking_id = str(uuid.uuid4())
        
        context_data = {
            "link_id": str(link.id),
            "short_code": link.short_code,
            "original_url": link.original_url,
            "click_id": str(click.id),
            "platform": click.platform,
            "device_type": click.device_type,
            "country": click.country,
            "created_at": datetime.utcnow().isoformat(),
            "utm_params": {
                "utm_source": link.utm_source,
                "utm_medium": link.utm_medium,
                "utm_campaign": link.utm_campaign,
                "utm_term": link.utm_term,
                "utm_content": link.utm_content
            }
        }
        
        if additional_data:
            context_data.update(additional_data)
        
        # Stocker dans Redis avec TTL
        self.redis_client.setex(
            f"deferred_context:{tracking_id}",
            self.tracking_cookie_ttl,
            json.dumps(context_data)
        )
        
        return tracking_id
    
    def get_deferred_context(self, tracking_id: str) -> Optional[Dict]:
        """
        Récupère le contexte de deep linking différé
        """
        context_data = self.redis_client.get(f"deferred_context:{tracking_id}")
        if context_data:
            return json.loads(context_data)
        return None
    
    def generate_install_redirect_url(
        self, 
        link: DynamicLink, 
        platform: str,
        tracking_id: str
    ) -> str:
        """
        Génère l'URL de redirection vers le store avec tracking
        """
        base_url = ""
        
        if platform == "android" and link.android_fallback_url:
            base_url = link.android_fallback_url
        elif platform == "ios" and link.ios_fallback_url:
            base_url = link.ios_fallback_url
        else:
            # URLs par défaut des stores
            if platform == "android":
                package = link.android_package or "com.example.app"
                base_url = f"https://play.google.com/store/apps/details?id={package}"
            elif platform == "ios":
                bundle_id = link.ios_bundle_id or "123456789"
                base_url = f"https://apps.apple.com/app/id{bundle_id}"
        
        # Ajouter le tracking ID comme paramètre
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}synctra_tracking={tracking_id}"
    
    def create_deferred_link_page(
        self, 
        link: DynamicLink, 
        tracking_id: str,
        platform: str
    ) -> str:
        """
        Génère une page HTML intermédiaire pour le deferred deep linking
        """
        install_url = self.generate_install_redirect_url(link, platform, tracking_id)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{link.title or 'Redirection'}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }}
                .container {{
                    max-width: 400px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 30px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }}
                .logo {{
                    width: 80px;
                    height: 80px;
                    background: white;
                    border-radius: 20px;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 30px;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 10px;
                }}
                .description {{
                    font-size: 16px;
                    opacity: 0.9;
                    margin-bottom: 30px;
                }}
                .install-btn {{
                    background: white;
                    color: #333;
                    padding: 15px 30px;
                    border: none;
                    border-radius: 50px;
                    font-size: 16px;
                    font-weight: 600;
                    text-decoration: none;
                    display: inline-block;
                    transition: transform 0.2s;
                }}
                .install-btn:hover {{
                    transform: translateY(-2px);
                }}
                .continue-web {{
                    margin-top: 20px;
                    opacity: 0.8;
                }}
                .continue-web a {{
                    color: white;
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">📱</div>
                <div class="title">{link.title or 'Application requise'}</div>
                <div class="description">
                    {link.description or 'Pour une meilleure expérience, téléchargez notre application.'}
                </div>
                <a href="{install_url}" class="install-btn" onclick="trackAppInstall()">
                    {'Télécharger sur l\'App Store' if platform == 'ios' else 'Télécharger sur Google Play'}
                </a>
                <div class="continue-web">
                    <a href="{link.original_url}" onclick="trackWebContinue()">
                        Continuer sur le web
                    </a>
                </div>
            </div>
            
            <script>
                // Stocker le tracking ID dans le localStorage
                localStorage.setItem('synctra_tracking_id', '{tracking_id}');
                
                var appOpened = false;
                var startTime = Date.now();
                
                // Essayer d'ouvrir l'app automatiquement si elle est installée
                function tryOpenApp() {{
                    var appScheme = '';
                    var fallbackUrl = '';
                    
                    if ('{platform}' === 'ios' && '{link.ios_bundle_id or ""}') {{
                        // Pour iOS, utiliser un custom scheme ou universal link
                        appScheme = '{link.ios_bundle_id or ""}://open?url=' + encodeURIComponent('{link.original_url}');
                        fallbackUrl = '{link.ios_fallback_url or link.original_url}';
                    }} else if ('{platform}' === 'android' && '{link.android_package or ""}') {{
                        // Pour Android, utiliser intent URL
                        appScheme = 'intent://{link.original_url}#Intent;package={link.android_package or ""};scheme=https;end';
                        fallbackUrl = '{link.android_fallback_url or link.original_url}';
                    }}
                    
                    if (appScheme) {{
                        // Créer un iframe invisible pour tester l'ouverture
                        var iframe = document.createElement('iframe');
                        iframe.style.display = 'none';
                        iframe.src = appScheme;
                        document.body.appendChild(iframe);
                        
                        // Détecter si l'app s'est ouverte
                        setTimeout(function() {{
                            if (!appOpened && (Date.now() - startTime) < 3000) {{
                                // L'app ne s'est pas ouverte, on reste sur la page
                                document.body.removeChild(iframe);
                            }}
                        }}, 2000);
                        
                        // Détecter si l'utilisateur revient (app fermée)
                        window.addEventListener('focus', function() {{
                            if (Date.now() - startTime > 1000) {{
                                appOpened = true;
                            }}
                        }});
                        
                        // Détecter la perte de focus (app ouverte)
                        window.addEventListener('blur', function() {{
                            appOpened = true;
                        }});
                    }}
                }}
                
                // Lancer la tentative d'ouverture après un délai
                setTimeout(tryOpenApp, 500);
                
                function trackWebContinue() {{
                    fetch('/api/v1/deferred/track-web-continue', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{tracking_id: '{tracking_id}'}})
                    }});
                }}
                
                function trackAppInstall() {{
                    fetch('/api/v1/deferred/track-app-install', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{tracking_id: '{tracking_id}'}})
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        return html_content
    
    def handle_app_open(
        self, 
        tracking_id: str, 
        app_identifier: str,
        db: Session
    ) -> Optional[Dict]:
        """
        Gère l'ouverture de l'app après installation avec le contexte différé
        """
        context = self.get_deferred_context(tracking_id)
        if not context:
            return None
        
        # Marquer comme conversion réussie
        click_id = context.get("click_id")
        if click_id:
            click = db.query(LinkClick).filter(LinkClick.id == click_id).first()
            if click:
                click.converted = True
                db.commit()
        
        # Nettoyer le contexte utilisé
        self.redis_client.delete(f"deferred_context:{tracking_id}")
        
        return {
            "success": True,
            "original_url": context.get("original_url"),
            "utm_params": context.get("utm_params", {}),
            "link_data": {
                "short_code": context.get("short_code"),
                "platform": context.get("platform")
            }
        }

deferred_service = DeferredDeepLinkingService()
