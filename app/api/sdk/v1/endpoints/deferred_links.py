from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.sdk_auth import get_api_key_auth
from app.models.project import Project
from app.models.dynamic_link import DynamicLink
from app.schemas.sdk import DeferredLinkCreate, DeferredLinkQuery, SDKResponse, DeepLinkResponse
from app.services.link_generator import LinkGenerator
from app.core.config import settings

router = APIRouter()

@router.get("", include_in_schema=False)
@router.get("/")
async def get_deferred_link(
    packageName: str = Query(..., description="Nom du package"),
    deviceId: str = Query(..., description="ID de l'appareil"),
    platform: str = Query(..., description="Plateforme"),
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Récupérer un lien différé pour un appareil."""
    
    # TODO: Implémenter la logique de récupération des liens différés
    # Pour l'instant, retourner une erreur 404
    
    raise HTTPException(
        status_code=404,
        detail={
            "success": False,
            "message": "Aucun lien différé trouvé",
            "code": "NO_DEFERRED_LINK"
        }
    )

@router.post("", status_code=201, include_in_schema=False)
@router.post("/", status_code=201)
async def store_deferred_link(
    deferred_data: DeferredLinkCreate,
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Stocker des données de lien différé."""
    
    # Vérifier que le lien existe dans ce projet
    link = db.query(DynamicLink).filter(
        DynamicLink.id == deferred_data.linkId,
        DynamicLink.project_id == project.id
    ).first()
    
    if not link:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Lien non trouvé",
                "code": "LINK_NOT_FOUND"
            }
        )
    
    # TODO: Créer un modèle DeferredLink et stocker les données
    # Pour l'instant, juste confirmer la réception
    
    return SDKResponse(success=True)

@router.delete("", status_code=204, include_in_schema=False)
@router.delete("/", status_code=204)
async def clean_deferred_link(
    packageName: str = Query(..., description="Nom du package"),
    deviceId: str = Query(..., description="ID de l'appareil"),
    project: Project = Depends(get_api_key_auth),
    db: Session = Depends(get_db)
):
    """Nettoyer les données de lien différé."""
    
    # TODO: Implémenter la suppression des données différées
    pass
