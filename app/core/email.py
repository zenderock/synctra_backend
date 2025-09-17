from app.core.onesignal import onesignal_service
from typing import Optional
import asyncio


async def send_invitation_email(
    email: str,
    organization_name: str,
    inviter_name: str,
    token: str,
    role: str = "member"
) -> bool:
    """
    Envoie un email d'invitation pour rejoindre une organisation via OneSignal
    """
    try:
        return await onesignal_service.send_invitation_email(
            email=email,
            first_name="",  # Sera rempli lors de l'acceptation
            organization_name=organization_name,
            invitation_token=token,
            role=role
        )
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email d'invitation: {e}")
        return False


async def send_welcome_email(email: str, first_name: str, organization_name: str) -> bool:
    """
    Envoie un email de bienvenue après acceptation d'invitation via OneSignal
    """
    try:
        subject = f"Bienvenue dans {organization_name} sur Synctra !"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bienvenue sur Synctra</title>
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
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">Synctra</div>
            </div>
            
            <div class="content">
                <h1>Bienvenue {first_name} !</h1>
                
                <p>Félicitations ! Vous faites maintenant partie de l'organisation <strong>{organization_name}</strong> sur Synctra.</p>
                
                <p>Vous pouvez maintenant :</p>
                <ul>
                    <li>Créer et gérer des liens dynamiques</li>
                    <li>Suivre les analytics en temps réel</li>
                    <li>Gérer des programmes de parrainage</li>
                    <li>Collaborer avec votre équipe</li>
                </ul>
                
                <div style="text-align: center;">
                    <a href="https://synctra-admin.vercel.app/dashboard" class="button">
                        Accéder au dashboard
                    </a>
                </div>
                
                <p>Si vous avez des questions, n'hésitez pas à contacter votre équipe ou consulter notre documentation.</p>
                
                <p>Bonne utilisation de Synctra !</p>
            </div>
            
            <div class="footer">
                <p>L'équipe Synctra</p>
            </div>
        </body>
        </html>
        """
        
        return await onesignal_service.send_email(
            email=email,
            subject=subject,
            html_content=html_content
        )
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")
        return False
