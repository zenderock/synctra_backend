from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass

class PlanType(str, Enum):
    STARTER = "starter"
    PRO = "pro"
    PLUS = "plus"

@dataclass
class PlanLimits:
    max_projects: int
    max_organization_members: int
    has_full_analytics: bool
    has_custom_domain: bool
    has_ip_restrictions: bool
    max_links_per_project: int = None  # None = illimité

PLAN_LIMITS: Dict[PlanType, PlanLimits] = {
    PlanType.STARTER: PlanLimits(
        max_projects=1,
        max_organization_members=2,
        has_full_analytics=False,
        has_custom_domain=False,
        has_ip_restrictions=False,
        max_links_per_project=2
    ),
    PlanType.PRO: PlanLimits(
        max_projects=5,
        max_organization_members=5,
        has_full_analytics=True,
        has_custom_domain=False,
        has_ip_restrictions=False,
        max_links_per_project=200
    ),
    PlanType.PLUS: PlanLimits(
        max_projects=None,  # Illimité
        max_organization_members=20,
        has_full_analytics=True,
        has_custom_domain=True,
        has_ip_restrictions=True,
        max_links_per_project=None  # Illimité
    )
}

PLAN_FEATURES: Dict[PlanType, Dict[str, Any]] = {
    PlanType.STARTER: {
        "name": "Starter Plan",
        "price": 0,
        "currency": "EUR",
        "billing_period": "monthly",
        "features": [
            "Création de deeplinks",
            "1 projet maximum",
            "Analytics de base",
            "2 membres maximum",
            "100 liens par projet"
        ]
    },
    PlanType.PRO: {
        "name": "Pro Plan",
        "price": 25,
        "currency": "EUR",
        "billing_period": "monthly",
        "features": [
            "Analytics complètes",
            "5 projets maximum",
            "5 membres maximum",
            "1000 liens par projet",
            "Support prioritaire"
        ]
    },
    PlanType.PLUS: {
        "name": "Plus Plan",
        "price": 50,
        "currency": "EUR",
        "billing_period": "monthly",
        "features": [
            "Projets illimités",
            "Domaines personnalisés",
            "Restrictions IP personnalisées",
            "20 membres maximum",
            "Liens illimités",
            "Support dédié"
        ]
    }
}
