from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import csv
import io
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.core.deps import get_project_by_id, get_current_active_user
from app.models.project import Project
from app.models.dynamic_link import DynamicLink
from app.models.link_click import LinkClick
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview, LinkAnalytics, ClickEvent, ExportRequest
from app.services.subscription_service import SubscriptionService

router = APIRouter()

@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    project: Project = Depends(get_project_by_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Nombre de jours à analyser")
):
    # Vérifier l'accès aux analytics complètes
    has_full_analytics = SubscriptionService.has_feature_access(
        db, str(current_user.organization_id), "full_analytics"
    )
    
    # Limiter les données pour le plan Starter
    if not has_full_analytics and days > 7:
        days = 7  # Limiter à 7 jours pour le plan Starter
    
    date_from = datetime.utcnow() - timedelta(days=days)
    
    total_links = db.query(DynamicLink).filter(
        DynamicLink.project_id == project.id
    ).count()
    
    total_clicks = db.query(LinkClick).join(DynamicLink).filter(
        DynamicLink.project_id == project.id,
        LinkClick.clicked_at >= date_from
    ).count()
    
    conversions = db.query(LinkClick).join(DynamicLink).filter(
        DynamicLink.project_id == project.id,
        LinkClick.clicked_at >= date_from,
        LinkClick.converted == True
    ).count()
    
    conversion_rate = (conversions / total_clicks * 100) if total_clicks > 0 else 0
    
    top_countries = db.query(
        LinkClick.country,
        func.count(LinkClick.id).label('count')
    ).join(DynamicLink).filter(
        DynamicLink.project_id == project.id,
        LinkClick.clicked_at >= date_from,
        LinkClick.country.isnot(None)
    ).group_by(LinkClick.country).order_by(desc('count')).limit(5).all()
    
    top_platforms = db.query(
        LinkClick.platform,
        func.count(LinkClick.id).label('count')
    ).join(DynamicLink).filter(
        DynamicLink.project_id == project.id,
        LinkClick.clicked_at >= date_from,
        LinkClick.platform.isnot(None)
    ).group_by(LinkClick.platform).order_by(desc('count')).limit(5).all()
    
    clicks_by_day = db.query(
        func.date(LinkClick.clicked_at).label('date'),
        func.count(LinkClick.id).label('count')
    ).join(DynamicLink).filter(
        DynamicLink.project_id == project.id,
        LinkClick.clicked_at >= date_from
    ).group_by(func.date(LinkClick.clicked_at)).order_by('date').all()
    
    return AnalyticsOverview(
        total_clicks=total_clicks,
        total_links=total_links,
        conversion_rate=round(conversion_rate, 2),
        top_countries=[{"country": c.country, "count": c.count} for c in top_countries],
        top_platforms=[{"platform": p.platform, "count": p.count} for p in top_platforms],
        clicks_over_time=[{"date": str(d.date), "count": d.count} for d in clicks_by_day]
    )

@router.get("/links", response_model=List[LinkAnalytics])
async def get_links_analytics(
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Nombre de jours à analyser")
):
    date_from = datetime.utcnow() - timedelta(days=days)
    
    links_with_stats = db.query(
        DynamicLink.id,
        DynamicLink.short_code,
        DynamicLink.title,
        func.count(LinkClick.id).label('total_clicks'),
        func.count(func.distinct(LinkClick.ip_address)).label('unique_clicks'),
        func.sum(func.cast(LinkClick.converted, db.Integer)).label('conversions')
    ).outerjoin(LinkClick).filter(
        DynamicLink.project_id == project.id
    ).group_by(DynamicLink.id, DynamicLink.short_code, DynamicLink.title).all()
    
    result = []
    for link_stat in links_with_stats:
        conversion_rate = 0
        if link_stat.total_clicks > 0:
            conversion_rate = (link_stat.conversions or 0) / link_stat.total_clicks * 100
        
        top_countries = db.query(
            LinkClick.country,
            func.count(LinkClick.id).label('count')
        ).filter(
            LinkClick.link_id == link_stat.id,
            LinkClick.clicked_at >= date_from,
            LinkClick.country.isnot(None)
        ).group_by(LinkClick.country).order_by(desc('count')).limit(3).all()
        
        top_platforms = db.query(
            LinkClick.platform,
            func.count(LinkClick.id).label('count')
        ).filter(
            LinkClick.link_id == link_stat.id,
            LinkClick.clicked_at >= date_from,
            LinkClick.platform.isnot(None)
        ).group_by(LinkClick.platform).order_by(desc('count')).limit(3).all()
        
        clicks_by_day = db.query(
            func.date(LinkClick.clicked_at).label('date'),
            func.count(LinkClick.id).label('count')
        ).filter(
            LinkClick.link_id == link_stat.id,
            LinkClick.clicked_at >= date_from
        ).group_by(func.date(LinkClick.clicked_at)).order_by('date').all()
        
        result.append(LinkAnalytics(
            link_id=str(link_stat.id),
            short_code=link_stat.short_code,
            title=link_stat.title,
            total_clicks=link_stat.total_clicks or 0,
            unique_clicks=link_stat.unique_clicks or 0,
            conversion_rate=round(conversion_rate, 2),
            top_countries=[{"country": c.country, "count": c.count} for c in top_countries],
            top_platforms=[{"platform": p.platform, "count": p.count} for p in top_platforms],
            clicks_by_day=[{"date": str(d.date), "count": d.count} for d in clicks_by_day]
        ))
    
    return result

@router.get("/export")
async def export_analytics(
    project: Project = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    format: str = Query("csv", description="Format d'export (csv, json)"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None)
):
    query = db.query(LinkClick).join(DynamicLink).filter(
        DynamicLink.project_id == project.id
    )
    
    if date_from:
        query = query.filter(LinkClick.clicked_at >= date_from)
    if date_to:
        query = query.filter(LinkClick.clicked_at <= date_to)
    
    clicks = query.all()
    
    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "ID", "Lien ID", "IP", "Pays", "Région", "Ville", 
            "Plateforme", "Type d'appareil", "Navigateur", "OS",
            "Converti", "Valeur conversion", "Date de clic"
        ])
        
        for click in clicks:
            writer.writerow([
                str(click.id), str(click.link_id), click.ip_address,
                click.country, click.region, click.city,
                click.platform, click.device_type, click.browser, click.os,
                click.converted, click.conversion_value, click.clicked_at
            ])
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics_export.csv"}
        )
    
    return {"message": "Format non supporté"}
