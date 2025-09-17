import httpx
import json
from typing import Dict, Any, Optional
from app.core.config import settings


class OneSignalService:
    def __init__(self):
        self.app_id = settings.ONESIGNAL_APP_ID
        self.rest_api_key = settings.ONESIGNAL_REST_API_KEY
        self.base_url = "https://api.onesignal.com"
    
    async def send_email(
        self,
        email: str,
        subject: str,
        html_content: str,
        template_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envoie un email via OneSignal
        """
        try:
            headers = {
                "Authorization": f"Basic {self.rest_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "app_id": self.app_id,
                "target_channel": "email",
                "email_to": [email],
                "email_subject": subject,
                "email_body": html_content,
                "email_from_name": "Synctra",
                "email_from_address": "noreply@synctra.com"
            }
            
            if template_data:
                payload["custom_data"] = template_data
            
            querystring = {"c": "email"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/notifications",
                    headers=headers,
                    json=payload,
                    params=querystring,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("id") is not None
                else:
                    print(f"Erreur OneSignal: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"Erreur lors de l'envoi d'email OneSignal: {str(e)}")
            return False
    
    async def send_invitation_email(
        self,
        email: str,
        first_name: str,
        organization_name: str,
        invitation_token: str,
        role: str
    ) -> bool:
        """
        Envoie un email d'invitation spécifique
        """
        subject = f"Invitation à rejoindre {organization_name} sur Synctra"
        
        # Template HTML pour l'invitation
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Invitation Synctra</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    padding: 40px 0;
                    border-bottom: 1px solid #eee;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .content {{
                    padding: 40px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 500;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px 0;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 14px;
                }}
                .role-badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    background-color: #f3f4f6;
                    color: #374151;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">Synctra</div>
            </div>
            
            <div class="content">
                <h1>Vous êtes invité(e) à rejoindre {organization_name}</h1>
                
                <p>Bonjour {first_name},</p>
                
                <p>Vous avez été invité(e) à rejoindre l'organisation <strong>{organization_name}</strong> sur Synctra en tant que <span class="role-badge">{role}</span>.</p>
                
                <p>Synctra est une plateforme de gestion de liens dynamiques et de codes de parrainage qui vous permettra de :</p>
                <ul>
                    <li>Créer et gérer des liens dynamiques</li>
                    <li>Suivre les analytics en temps réel</li>
                    <li>Gérer des programmes de parrainage</li>
                    <li>Collaborer avec votre équipe</li>
                </ul>
                
                <p>Pour accepter cette invitation et créer votre compte, cliquez sur le bouton ci-dessous :</p>
                
                <div style="text-align: center;">
                    <a href="{settings.FRONTEND_URL}/invitation/accept?token={invitation_token}" class="button">
                        Accepter l'invitation
                    </a>
                </div>
                
                <p><strong>Important :</strong> Cette invitation expire dans 7 jours. Si vous ne pouvez pas cliquer sur le bouton, copiez et collez ce lien dans votre navigateur :</p>
                <p style="word-break: break-all; color: #666; font-size: 14px;">
                    {settings.FRONTEND_URL}/invitation/accept?token={invitation_token}
                </p>
                
                <p>Si vous avez des questions, n'hésitez pas à contacter l'équipe qui vous a invité.</p>
                
                <p>À bientôt sur Synctra !</p>
            </div>
            
            <div class="footer">
                <p>Cet email a été envoyé par Synctra. Si vous n'attendiez pas cette invitation, vous pouvez ignorer cet email.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            email=email,
            subject=subject,
            html_content=html_content
        )


# Instance globale du service
onesignal_service = OneSignalService()
