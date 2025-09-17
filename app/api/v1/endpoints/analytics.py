from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app import crud, models
from app.api import deps
from app.models.link_click import LinkClick
from app.models.dynamic_link import DynamicLink

router = APIRouter()


@router.get("/{project_id}/analytics/overview")
def get_project_analytics_overview(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    days: int = Query(default=30, description="Nombre de jours pour les statistiques"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Date de début pour les statistiques
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Statistiques générales
    total_links = db.query(DynamicLink).filter(DynamicLink.project_id == project_id).count()
    active_links = db.query(DynamicLink).filter(
        DynamicLink.project_id == project_id,
        DynamicLink.is_active == True
    ).count()
    
    # Statistiques des clics
    total_clicks = db.query(LinkClick).join(DynamicLink).filter(
        DynamicLink.project_id == project_id,
        LinkClick.clicked_at >= start_date
    ).count()
    
    # Clics par jour
    clicks_by_day = db.query(
        func.date(LinkClick.clicked_at).label('date'),
        func.count(LinkClick.id).label('clicks')
    ).join(DynamicLink).filter(
        DynamicLink.project_id == project_id,
        LinkClick.clicked_at >= start_date
    ).group_by(func.date(LinkClick.clicked_at)).order_by('date').all()
    
    # Top pays
    top_countries = db.query(
        LinkClick.country,
        func.count(LinkClick.id).label('clicks')
    ).join(DynamicLink).filter(
        DynamicLink.project_id == project_id,
        LinkClick.clicked_at >= start_date,
        LinkClick.country.isnot(None)
    ).group_by(LinkClick.country).order_by(desc('clicks')).limit(10).all()
    
    # Top plateformes
    top_platforms = db.query(
        LinkClick.platform,
        func.count(LinkClick.id).label('clicks')
    ).join(DynamicLink).filter(
        DynamicLink.project_id == project_id,
        LinkClick.clicked_at >= start_date,
        LinkClick.platform.isnot(None)
    ).group_by(LinkClick.platform).order_by(desc('clicks')).limit(10).all()
    
    # Top liens
    top_links = db.query(
        DynamicLink.id,
        DynamicLink.title,
        DynamicLink.short_code,
        func.count(LinkClick.id).label('clicks')
    ).outerjoin(LinkClick).filter(
        DynamicLink.project_id == project_id,
        LinkClick.clicked_at >= start_date
    ).group_by(DynamicLink.id).order_by(desc('clicks')).limit(10).all()
    
    return {
        "period_days": days,
        "total_links": total_links,
        "active_links": active_links,
        "total_clicks": total_clicks,
        "clicks_by_day": [{"date": str(item.date), "clicks": item.clicks} for item in clicks_by_day],
        "top_countries": [{"country": item.country, "clicks": item.clicks} for item in top_countries],
        "top_platforms": [{"platform": item.platform, "clicks": item.clicks} for item in top_platforms],
        "top_links": [
            {
                "id": str(item.id),
                "title": item.title,
                "short_code": item.short_code,
                "clicks": item.clicks or 0
            } for item in top_links
        ]
    }


@router.get("/{project_id}/analytics/links/{link_id}")
def get_link_analytics(
    *,
    db: Session = Depends(deps.get_db),
    project_id: str,
    link_id: str,
    days: int = Query(default=30, description="Nombre de jours pour les statistiques"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    if str(project.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    link = crud.dynamic_link.get(db, id=link_id)
    if not link or str(link.project_id) != project_id:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Statistiques du lien
    total_clicks = db.query(LinkClick).filter(
        LinkClick.link_id == link_id,
        LinkClick.clicked_at >= start_date
    ).count()
    
    # Clics par jour
    clicks_by_day = db.query(
        func.date(LinkClick.clicked_at).label('date'),
        func.count(LinkClick.id).label('clicks')
    ).filter(
        LinkClick.link_id == link_id,
        LinkClick.clicked_at >= start_date
    ).group_by(func.date(LinkClick.clicked_at)).order_by('date').all()
    
    # Répartition par plateforme
    platform_distribution = db.query(
        LinkClick.platform,
        func.count(LinkClick.id).label('clicks')
    ).filter(
        LinkClick.link_id == link_id,
        LinkClick.clicked_at >= start_date,
        LinkClick.platform.isnot(None)
    ).group_by(LinkClick.platform).all()
    
    # Répartition par pays
    country_distribution = db.query(
        LinkClick.country,
        func.count(LinkClick.id).label('clicks')
    ).filter(
        LinkClick.link_id == link_id,
        LinkClick.clicked_at >= start_date,
        LinkClick.country.isnot(None)
    ).group_by(LinkClick.country).order_by(desc('clicks')).limit(10).all()
    
    return {
        "link_id": link_id,
        "link_title": link.title,
        "short_code": link.short_code,
        "period_days": days,
        "total_clicks": total_clicks,
        "clicks_by_day": [{"date": str(item.date), "clicks": item.clicks} for item in clicks_by_day],
        "platform_distribution": [{"platform": item.platform, "clicks": item.clicks} for item in platform_distribution],
        "country_distribution": [{"country": item.country, "clicks": item.clicks} for item in country_distribution]
    }
