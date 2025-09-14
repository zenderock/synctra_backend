from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.project import Project

router = APIRouter()

@router.get("/.well-known/assetlinks.json")
async def get_assetlinks_json(request: Request, db: Session = Depends(get_db)):
    """Servir le fichier assetlinks.json pour Android App Links."""
    host = request.headers.get("host")
    
    project = db.query(Project).filter(
        (Project.domain == host) | (Project.custom_domain == host)
    ).first()
    
    if not project or not project.assetlinks_json:
        raise HTTPException(status_code=404, detail="Fichier assetlinks.json non trouvé")
    
    return project.assetlinks_json

@router.get("/.well-known/apple-app-site-association")
async def get_apple_app_site_association(request: Request, db: Session = Depends(get_db)):
    """Servir le fichier apple-app-site-association pour iOS Universal Links."""
    host = request.headers.get("host")
    
    project = db.query(Project).filter(
        (Project.domain == host) | (Project.custom_domain == host)
    ).first()
    
    if not project or not project.apple_app_site_association:
        raise HTTPException(status_code=404, detail="Fichier apple-app-site-association non trouvé")
    
    return project.apple_app_site_association

@router.get("/apple-app-site-association")
async def get_apple_app_site_association_root(request: Request, db: Session = Depends(get_db)):
    """Servir le fichier apple-app-site-association à la racine (fallback)."""
    return await get_apple_app_site_association(request, db)
