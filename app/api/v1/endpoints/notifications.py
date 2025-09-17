from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=List[schemas.Notification])
def read_notifications(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    unread_only: bool = Query(default=False),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Récupérer les notifications de l'utilisateur connecté.
    """
    notifications = crud.notification.get_by_user(
        db=db, 
        user_id=str(current_user.id), 
        skip=skip, 
        limit=limit,
        unread_only=unread_only
    )
    return notifications


@router.get("/unread-count", response_model=dict)
def get_unread_count(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Obtenir le nombre de notifications non lues.
    """
    count = crud.notification.get_unread_count(
        db=db, 
        user_id=str(current_user.id)
    )
    return {"unread_count": count}


@router.post("/", response_model=schemas.Notification)
def create_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_in: schemas.NotificationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Créer une nouvelle notification.
    """
    # Vérifier que l'utilisateur ne peut créer des notifications que pour lui-même
    # ou s'il a les permissions d'admin
    if notification_in.user_id != str(current_user.id) and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Vous ne pouvez pas créer de notifications pour d'autres utilisateurs"
        )
    
    notification = crud.notification.create(db=db, obj_in=notification_in)
    return notification


@router.put("/{notification_id}/read", response_model=schemas.Notification)
def mark_notification_as_read(
    *,
    db: Session = Depends(deps.get_db),
    notification_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Marquer une notification comme lue.
    """
    notification = crud.notification.mark_as_read(
        db=db, 
        notification_id=notification_id, 
        user_id=str(current_user.id)
    )
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification non trouvée"
        )
    
    return notification


@router.put("/mark-all-read", response_model=dict)
def mark_all_notifications_as_read(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Marquer toutes les notifications comme lues.
    """
    updated_count = crud.notification.mark_all_as_read(
        db=db, 
        user_id=str(current_user.id)
    )
    
    return {"updated_count": updated_count}


@router.delete("/{notification_id}")
def delete_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Supprimer une notification.
    """
    success = crud.notification.delete_by_user(
        db=db, 
        notification_id=notification_id, 
        user_id=str(current_user.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Notification non trouvée"
        )
    
    return {"message": "Notification supprimée avec succès"}


@router.post("/system", response_model=schemas.Notification)
def create_system_notification(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    category: str = "system",
    action_url: str = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Créer une notification système (admin seulement).
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Seuls les administrateurs peuvent créer des notifications système"
        )
    
    notification = crud.notification.create_system_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        category=category,
        action_url=action_url
    )
    
    return notification
