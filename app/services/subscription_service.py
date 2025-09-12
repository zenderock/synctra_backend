from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.subscription import Subscription
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.models.dynamic_link import DynamicLink
from app.core.subscription_plans import PlanType, PLAN_LIMITS, PLAN_FEATURES
from fastapi import HTTPException

class SubscriptionService:
    
    @staticmethod
    def get_organization_subscription(db: Session, organization_id: str) -> Optional[Subscription]:
        return db.query(Subscription).filter(
            Subscription.organization_id == organization_id
        ).first()
    
    @staticmethod
    def get_plan_limits(plan_type: PlanType):
        return PLAN_LIMITS.get(plan_type)
    
    @staticmethod
    def get_plan_features(plan_type: PlanType):
        return PLAN_FEATURES.get(plan_type)
    
    @staticmethod
    def check_project_limit(db: Session, organization_id: str) -> bool:
        subscription = SubscriptionService.get_organization_subscription(db, organization_id)
        if not subscription:
            # Si pas d'abonnement, vérifier le plan de l'organisation directement
            from app.models.organization import Organization
            org = db.query(Organization).filter(Organization.id == organization_id).first()
            if not org:
                return False
            plan_type = PlanType.STARTER if org.plan_type == "free" else PlanType(org.plan_type)
        else:
            plan_type = PlanType(subscription.plan_type)
            
        plan_limits = SubscriptionService.get_plan_limits(plan_type)
        if plan_limits.max_projects is None:
            return True
            
        current_projects = db.query(Project).filter(
            Project.organization_id == organization_id
        ).count()
        
        return current_projects < plan_limits.max_projects
    
    @staticmethod
    def check_member_limit(db: Session, organization_id: str) -> bool:
        subscription = SubscriptionService.get_organization_subscription(db, organization_id)
        if not subscription:
            # Si pas d'abonnement, vérifier le plan de l'organisation directement
            from app.models.organization import Organization
            org = db.query(Organization).filter(Organization.id == organization_id).first()
            if not org:
                return False
            plan_type = PlanType.STARTER if org.plan_type == "free" else PlanType(org.plan_type)
        else:
            plan_type = PlanType(subscription.plan_type)
            
        plan_limits = SubscriptionService.get_plan_limits(plan_type)
        
        current_members = db.query(User).filter(
            User.organization_id == organization_id
        ).count()
        
        return current_members < plan_limits.max_organization_members
    
    @staticmethod
    def check_links_limit(db: Session, project_id: str) -> bool:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
            
        subscription = SubscriptionService.get_organization_subscription(db, project.organization_id)
        if not subscription:
            return False
            
        plan_limits = SubscriptionService.get_plan_limits(PlanType(subscription.plan_type))
        if plan_limits.max_links_per_project is None:
            return True
            
        current_links = db.query(DynamicLink).filter(
            DynamicLink.project_id == project_id,
            DynamicLink.is_active == True
        ).count()
        
        return current_links < plan_limits.max_links_per_project
    
    @staticmethod
    def has_feature_access(db: Session, organization_id: str, feature: str) -> bool:
        subscription = SubscriptionService.get_organization_subscription(db, organization_id)
        if not subscription:
            # Si pas d'abonnement, vérifier le plan de l'organisation directement
            from app.models.organization import Organization
            org = db.query(Organization).filter(Organization.id == organization_id).first()
            if not org:
                return False
            plan_type = PlanType.STARTER if org.plan_type == "free" else PlanType(org.plan_type)
        else:
            plan_type = PlanType(subscription.plan_type)
            
        plan_limits = SubscriptionService.get_plan_limits(plan_type)
        
        feature_map = {
            "full_analytics": plan_limits.has_full_analytics,
            "custom_domain": plan_limits.has_custom_domain,
            "ip_restrictions": plan_limits.has_ip_restrictions
        }
        
        return feature_map.get(feature, False)
    
    @staticmethod
    def get_usage_stats(db: Session, organization_id: str) -> Dict[str, Any]:
        subscription = SubscriptionService.get_organization_subscription(db, organization_id)
        if not subscription:
            return {}
            
        plan_limits = SubscriptionService.get_plan_limits(PlanType(subscription.plan_type))
        
        projects_count = db.query(Project).filter(
            Project.organization_id == organization_id
        ).count()
        
        members_count = db.query(User).filter(
            User.organization_id == organization_id
        ).count()
        
        total_links = db.query(func.count(DynamicLink.id)).join(Project).filter(
            Project.organization_id == organization_id,
            DynamicLink.is_active == True
        ).scalar()
        
        return {
            "plan_type": subscription.plan_type,
            "projects": {
                "used": projects_count,
                "limit": plan_limits.max_projects,
                "unlimited": plan_limits.max_projects is None
            },
            "members": {
                "used": members_count,
                "limit": plan_limits.max_organization_members
            },
            "links": {
                "used": total_links or 0,
                "limit": plan_limits.max_links_per_project,
                "unlimited": plan_limits.max_links_per_project is None
            },
            "features": {
                "full_analytics": plan_limits.has_full_analytics,
                "custom_domain": plan_limits.has_custom_domain,
                "ip_restrictions": plan_limits.has_ip_restrictions
            }
        }
    
    @staticmethod
    def create_default_subscription(db: Session, organization_id: str) -> Subscription:
        subscription = Subscription(
            organization_id=organization_id,
            plan_type=PlanType.STARTER.value,
            status='active',
            amount=0,
            currency='EUR',
            billing_interval='monthly',
            projects_used=0,
            members_used=1
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def upgrade_subscription(
        db: Session, 
        organization_id: str, 
        new_plan: PlanType,
        external_payment_id: Optional[str] = None
    ) -> Subscription:
        subscription = SubscriptionService.get_organization_subscription(db, organization_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Abonnement non trouvé")
        
        plan_features = SubscriptionService.get_plan_features(new_plan)
        
        subscription.plan_type = new_plan.value
        subscription.amount = plan_features["price"]
        # Stocker la référence de paiement externe si fournie
        if external_payment_id:
            subscription.stripe_subscription_id = external_payment_id  # Réutiliser ce champ pour l'ID externe
        
        db.commit()
        db.refresh(subscription)
        
        return subscription
