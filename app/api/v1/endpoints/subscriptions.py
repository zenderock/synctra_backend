from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.subscription_service import SubscriptionService
from app.schemas.subscription import (
    SubscriptionResponse, 
    PlanLimitsResponse, 
    PlanFeaturesResponse,
    UsageStatsResponse,
    UpgradeRequest
)
from app.core.subscription_plans import PlanType, PLAN_LIMITS, PLAN_FEATURES

router = APIRouter()

@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer l'abonnement actuel de l'organisation"""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Utilisateur non associé à une organisation")
    
    subscription = SubscriptionService.get_organization_subscription(
        db, str(current_user.organization_id)
    )
    
    if not subscription:
        # Créer un abonnement par défaut si inexistant
        subscription = SubscriptionService.create_default_subscription(
            db, str(current_user.organization_id)
        )
    
    return subscription

@router.get("/plans", response_model=List[PlanFeaturesResponse])
async def get_available_plans():
    """Récupérer tous les plans disponibles"""
    plans = []
    for plan_type in PlanType:
        features = PLAN_FEATURES[plan_type]
        plans.append(PlanFeaturesResponse(**features))
    
    return plans

@router.get("/plans/{plan_type}/limits", response_model=PlanLimitsResponse)
async def get_plan_limits(plan_type: PlanType):
    """Récupérer les limites d'un plan spécifique"""
    limits = PLAN_LIMITS.get(plan_type)
    if not limits:
        raise HTTPException(status_code=404, detail="Plan non trouvé")
    
    return PlanLimitsResponse(
        max_projects=limits.max_projects,
        max_organization_members=limits.max_organization_members,
        has_full_analytics=limits.has_full_analytics,
        has_custom_domain=limits.has_custom_domain,
        has_ip_restrictions=limits.has_ip_restrictions,
        max_links_per_project=limits.max_links_per_project
    )

@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les statistiques d'usage de l'organisation"""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Utilisateur non associé à une organisation")
    
    stats = SubscriptionService.get_usage_stats(
        db, str(current_user.organization_id)
    )
    
    return UsageStatsResponse(**stats)

@router.post("/upgrade")
async def upgrade_subscription(
    upgrade_data: UpgradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à niveau l'abonnement"""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Utilisateur non associé à une organisation")
    
    # Vérifier que l'utilisateur a les droits d'admin
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=403, 
            detail="Seuls les administrateurs peuvent modifier l'abonnement"
        )
    
    try:
        # Ici on intégrerait Stripe pour le paiement
        # stripe_subscription_id = process_stripe_payment(upgrade_data.stripe_payment_method_id)
        
        subscription = SubscriptionService.upgrade_subscription(
            db=db,
            organization_id=str(current_user.organization_id),
            new_plan=upgrade_data.new_plan,
            stripe_subscription_id=None  # À remplacer par l'ID Stripe réel
        )
        
        return {
            "message": "Abonnement mis à niveau avec succès",
            "subscription": subscription
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la mise à niveau: {str(e)}")

@router.get("/features/{feature_name}")
async def check_feature_access(
    feature_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vérifier l'accès à une fonctionnalité spécifique"""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Utilisateur non associé à une organisation")
    
    has_access = SubscriptionService.has_feature_access(
        db, str(current_user.organization_id), feature_name
    )
    
    return {
        "feature": feature_name,
        "has_access": has_access
    }
