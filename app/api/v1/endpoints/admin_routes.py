from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Page d'accueil de l'administration"""
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@router.get("/links", response_class=HTMLResponse)
async def admin_links(request: Request):
    """Page de gestion des liens"""
    return templates.TemplateResponse("admin/links.html", {"request": request})

@router.get("/projects", response_class=HTMLResponse)
async def admin_projects(request: Request):
    """Page de gestion des projets"""
    return templates.TemplateResponse("admin/projects.html", {"request": request})

@router.get("/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request):
    """Page d'analytiques (à implémenter)"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analytiques - Synctra Admin</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
            .container { max-width: 600px; margin: 0 auto; }
            h1 { color: #667eea; }
            .back-btn { 
                background: #667eea; color: white; padding: 12px 24px; 
                text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Analytiques</h1>
            <p>Cette section sera bientôt disponible avec des graphiques détaillés et des rapports de performance.</p>
            <a href="/admin" class="back-btn">← Retour au dashboard</a>
        </div>
    </body>
    </html>
    """)

@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    """Page de gestion des utilisateurs (à implémenter)"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Utilisateurs - Synctra Admin</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
            .container { max-width: 600px; margin: 0 auto; }
            h1 { color: #667eea; }
            .back-btn { 
                background: #667eea; color: white; padding: 12px 24px; 
                text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👥 Gestion des utilisateurs</h1>
            <p>Cette section sera bientôt disponible pour gérer les comptes utilisateurs et leurs permissions.</p>
            <a href="/admin" class="back-btn">← Retour au dashboard</a>
        </div>
    </body>
    </html>
    """)
