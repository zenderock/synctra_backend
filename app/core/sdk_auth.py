from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.project import Project

async def get_api_key_auth(
    authorization: Optional[str] = Header(None),
    x_project_id: Optional[str] = Header(None, alias="X-Project-ID"),
    db: Session = Depends(get_db)
) -> Project:
    """
    Authentification par API key pour le SDK.
    Vérifie l'API key et le Project ID dans les headers.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": "Header Authorization manquant",
                "code": "MISSING_AUTH_HEADER"
            }
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": "Format d'autorisation invalide. Utilisez 'Bearer {API_KEY}'",
                "code": "INVALID_AUTH_FORMAT"
            }
        )
    
    if not x_project_id:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": "Header X-Project-ID manquant",
                "code": "MISSING_PROJECT_ID"
            }
        )
    
    api_key = authorization[7:]  # Enlever "Bearer "
    
    # Vérifier que l'API key correspond au projet
    project = db.query(Project).filter(
        Project.id == x_project_id,
        Project.api_key == api_key,
        Project.is_active == True
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": "API key ou Project ID invalide",
                "code": "INVALID_CREDENTIALS"
            }
        )
    
    return project
