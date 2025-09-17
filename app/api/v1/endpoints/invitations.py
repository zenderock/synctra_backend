from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
import secrets
import string
from datetime import datetime, timezone, timedelta

from app import crud, models, schemas
from app.api import deps
from app.core.email import send_invitation_email

router = APIRouter()


@router.post("/", response_model=schemas.Invitation)
def send_invitation(
    *,
    db: Session = Depends(deps.get_db),
    invitation_in: schemas.InvitationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Envoyer une invitation à rejoindre l'organisation
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation associée")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants pour inviter des membres")
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = crud.user.get_by_email(db, email=invitation_in.email)
    if existing_user and existing_user.organization_id == current_user.organization_id:
        raise HTTPException(status_code=400, detail="Cet utilisateur fait déjà partie de l'organisation")
    
    # Vérifier si une invitation est déjà en cours
    existing_invitation = crud.invitation.get_by_email_and_organization(
        db, email=invitation_in.email, organization_id=str(current_user.organization_id)
    )
    if existing_invitation and existing_invitation.status == "pending":
        raise HTTPException(status_code=400, detail="Une invitation est déjà en cours pour cet email")
    
    # Vérifier les limites du plan
    organization = crud.organization.get(db, id=current_user.organization_id)
    limits = crud.organization.get_plan_limits(organization.plan_type)
    current_members = crud.user.count_by_organization(db, organization_id=str(current_user.organization_id))
    
    if limits["max_members"] != -1 and current_members >= limits["max_members"]:
        raise HTTPException(
            status_code=402, 
            detail=f"Limite de membres atteinte pour le plan {organization.plan_type}"
        )
    
    # Générer un token d'invitation
    token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    # Créer l'invitation
    invitation = crud.invitation.create(
        db, 
        obj_in=invitation_in, 
        organization_id=str(current_user.organization_id),
        invited_by_id=str(current_user.id),
        token=token
    )
    
    # Récupérer les données nécessaires avant la tâche en arrière-plan
    organization_name = organization.name
    inviter_name = f"{current_user.first_name} {current_user.last_name}"
    invitation_token = invitation.token
    
    # Envoyer l'email d'invitation via OneSignal
    async def send_email_task():
        await send_invitation_email(
            invitation_in.email,
            organization_name,
            inviter_name,
            invitation_token,
            invitation_in.role
        )
    
    background_tasks.add_task(send_email_task)
    
    # Convertir manuellement l'objet pour éviter les erreurs UUID
    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "role": invitation.role,
        "token": invitation.token,
        "status": invitation.status,
        "organization_id": str(invitation.organization_id),
        "invited_by_id": str(invitation.invited_by_id),
        "accepted_by_id": str(invitation.accepted_by_id) if invitation.accepted_by_id else None,
        "invited_at": invitation.invited_at,
        "accepted_at": invitation.accepted_at,
        "expires_at": invitation.expires_at
    }


@router.get("/", response_model=List[schemas.Invitation])
def get_invitations(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Récupérer toutes les invitations de l'organisation
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation associée")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")
    
    invitations = crud.invitation.get_by_organization(db, organization_id=str(current_user.organization_id))
    return invitations


@router.post("/{invitation_id}/resend", response_model=schemas.Invitation)
def resend_invitation(
    *,
    db: Session = Depends(deps.get_db),
    invitation_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Renvoyer une invitation
    """
    invitation = crud.invitation.get(db, id=invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation non trouvée")
    
    if str(invitation.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")
    
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Cette invitation ne peut pas être renvoyée")
    
    # Générer un nouveau token
    new_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    # Mettre à jour l'invitation
    invitation = crud.invitation.update(
        db, 
        db_obj=invitation, 
        obj_in={"token": new_token, "invited_at": datetime.now(timezone.utc)}
    )
    
    # Renvoyer l'email
    organization = crud.organization.get(db, id=current_user.organization_id)
    background_tasks.add_task(
        send_invitation_email,
        email=invitation.email,
        organization_name=organization.name,
        inviter_name=f"{current_user.first_name} {current_user.last_name}",
        token=new_token
    )
    
    return invitation


@router.delete("/{invitation_id}")
def cancel_invitation(
    *,
    db: Session = Depends(deps.get_db),
    invitation_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Annuler une invitation
    """
    invitation = crud.invitation.get(db, id=invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation non trouvée")
    
    if str(invitation.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")
    
    crud.invitation.remove(db, id=invitation_id)
    return {"message": "Invitation annulée"}


@router.get("/validate/{token}")
def validate_invitation_token(
    *,
    db: Session = Depends(deps.get_db),
    token: str,
) -> Any:
    """
    Valider un token d'invitation et retourner les informations
    """
    invitation = crud.invitation.get_by_token(db, token=token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation non trouvée ou expirée")
    
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Cette invitation n'est plus valide")
    
    # Vérifier l'expiration (7 jours)
    if invitation.invited_at < datetime.now(timezone.utc) - timedelta(days=7):
        raise HTTPException(status_code=400, detail="Cette invitation a expiré")
    
    # Récupérer les informations de l'organisation et de l'inviteur
    organization = crud.organization.get(db, id=invitation.organization_id)
    invited_by = crud.user.get(db, id=invitation.invited_by_id)
    
    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "role": invitation.role,
        "organization_name": organization.name if organization else "Organisation inconnue",
        "invited_by_name": f"{invited_by.first_name} {invited_by.last_name}" if invited_by else "Utilisateur inconnu",
        "expires_at": invitation.invited_at + timedelta(days=7)
    }


@router.post("/accept/{token}", response_model=schemas.User)
def accept_invitation(
    *,
    db: Session = Depends(deps.get_db),
    token: str,
    user_data: schemas.UserCreateFromInvitation,
) -> Any:
    """
    Accepter une invitation et créer le compte utilisateur
    """
    # Trouver l'invitation par token
    invitation = crud.invitation.get_by_token(db, token=token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation non trouvée ou expirée")
    
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Cette invitation n'est plus valide")
    
    # Vérifier l'expiration (7 jours)
    if invitation.invited_at < datetime.now(timezone.utc) - timedelta(days=7):
        raise HTTPException(status_code=400, detail="Cette invitation a expiré")
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = crud.user.get_by_email(db, email=invitation.email)
    if existing_user:
        # Si l'utilisateur existe, l'ajouter à l'organisation
        if existing_user.organization_id:
            raise HTTPException(status_code=400, detail="Cet utilisateur fait déjà partie d'une organisation")
        
        # Mettre à jour l'utilisateur existant
        user = crud.user.update(
            db,
            db_obj=existing_user,
            obj_in={
                "organization_id": invitation.organization_id,
                "role": invitation.role
            }
        )
    else:
        # Créer un nouvel utilisateur
        user = crud.user.create_from_invitation(
            db,
            obj_in=user_data,
            email=invitation.email,
            organization_id=str(invitation.organization_id),
            role=invitation.role
        )
    
    # Marquer l'invitation comme acceptée
    crud.invitation.update(
        db,
        db_obj=invitation,
        obj_in={
            "status": "accepted",
            "accepted_at": datetime.now(timezone.utc),
            "accepted_by_id": str(user.id)
        }
    )
    
    return user
