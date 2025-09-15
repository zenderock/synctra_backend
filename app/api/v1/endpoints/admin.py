from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.dynamic_link import DynamicLink
from app.models.click import Click
from app.schemas.response import ApiResponse

router = APIRouter()

@router.get("/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    """Récupérer les statistiques générales pour le dashboard admin"""
    
    # Total des liens
    total_links = db.query(DynamicLink).count()
    
    # Total des projets
    total_projects = db.query(Project).count()
    
    # Clics aujourd'hui
    today = datetime.now().date()
    today_clicks = db.query(Click).filter(
        func.date(Click.created_at) == today
    ).count()
    
    # Taux de conversion (liens avec au moins 1 clic)
    links_with_clicks = db.query(DynamicLink).join(Click).distinct().count()
    conversion_rate = round((links_with_clicks / total_links * 100) if total_links > 0 else 0, 1)
    
    return ApiResponse.success(
        data={
            "totalLinks": total_links,
            "totalProjects": total_projects,
            "todayClicks": today_clicks,
            "conversionRate": conversion_rate
        },
        message="Statistiques récupérées avec succès"
    )

@router.get("/activity")
async def get_recent_activity(db: Session = Depends(get_db)):
    """Récupérer l'activité récente pour le dashboard"""
    
    activities = []
    
    # Liens récents (derniers 10)
    recent_links = db.query(DynamicLink).order_by(desc(DynamicLink.created_at)).limit(5).all()
    for link in recent_links:
        activities.append({
            "type": "link_created",
            "title": f"Nouveau lien créé",
            "description": f"{link.title or link.short_code} - {link.project.name if link.project else 'N/A'}",
            "created_at": link.created_at.isoformat()
        })
    
    # Projets récents (derniers 5)
    recent_projects = db.query(Project).order_by(desc(Project.created_at)).limit(3).all()
    for project in recent_projects:
        activities.append({
            "type": "project_created",
            "title": f"Nouveau projet créé",
            "description": f"{project.name}",
            "created_at": project.created_at.isoformat()
        })
    
    # Trier par date
    activities.sort(key=lambda x: x['created_at'], reverse=True)
    
    return ApiResponse.success(
        data=activities[:10],
        message="Activité récupérée avec succès"
    )

@router.get("/links")
async def get_admin_links(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    period: Optional[str] = Query(None)
):
    """Récupérer tous les liens avec filtres pour l'admin"""
    
    query = db.query(DynamicLink).join(Project, isouter=True)
    
    # Filtres
    if search:
        query = query.filter(
            (DynamicLink.title.ilike(f"%{search}%")) |
            (DynamicLink.short_code.ilike(f"%{search}%")) |
            (DynamicLink.original_url.ilike(f"%{search}%"))
        )
    
    if project:
        query = query.filter(DynamicLink.project_id == project)
    
    if status == "active":
        query = query.filter(DynamicLink.is_active == True)
    elif status == "inactive":
        query = query.filter(DynamicLink.is_active == False)
    
    if period:
        now = datetime.now()
        if period == "today":
            query = query.filter(func.date(DynamicLink.created_at) == now.date())
        elif period == "week":
            week_ago = now - timedelta(days=7)
            query = query.filter(DynamicLink.created_at >= week_ago)
        elif period == "month":
            month_ago = now - timedelta(days=30)
            query = query.filter(DynamicLink.created_at >= month_ago)
    
    # Pagination
    total = query.count()
    links = query.order_by(desc(DynamicLink.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    # Formater les données
    links_data = []
    for link in links:
        # Compter les clics
        click_count = db.query(Click).filter(Click.link_id == link.id).count()
        
        links_data.append({
            "id": str(link.id),
            "short_code": link.short_code,
            "short_url": f"https://synctra.focustagency.com/{link.short_code}",
            "original_url": link.original_url,
            "title": link.title,
            "description": link.description,
            "project_name": link.project.name if link.project else None,
            "is_active": link.is_active,
            "click_count": click_count,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "updated_at": link.updated_at.isoformat() if link.updated_at else None
        })
    
    return ApiResponse.success(
        data={
            "links": links_data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        },
        message="Liens récupérés avec succès"
    )

@router.get("/projects")
async def get_admin_projects(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None)
):
    """Récupérer tous les projets avec filtres pour l'admin"""
    
    query = db.query(Project)
    
    # Filtres
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))
    
    if status == "active":
        query = query.filter(Project.is_active == True)
    elif status == "inactive":
        query = query.filter(Project.is_active == False)
    
    if platform == "android":
        query = query.filter(Project.android_package.isnot(None))
    elif platform == "ios":
        query = query.filter(Project.ios_app_id.isnot(None))
    elif platform == "both":
        query = query.filter(
            (Project.android_package.isnot(None)) &
            (Project.ios_app_id.isnot(None))
        )
    
    projects = query.order_by(desc(Project.created_at)).all()
    
    # Formater les données avec statistiques
    projects_data = []
    for project in projects:
        # Compter les liens
        links_count = db.query(DynamicLink).filter(DynamicLink.project_id == project.id).count()
        
        # Compter les clics totaux
        total_clicks = db.query(func.count(Click.id)).join(DynamicLink).filter(
            DynamicLink.project_id == project.id
        ).scalar() or 0
        
        # Compter les utilisateurs (créateurs de liens)
        users_count = db.query(func.count(func.distinct(DynamicLink.created_by))).filter(
            DynamicLink.project_id == project.id
        ).scalar() or 0
        
        projects_data.append({
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "android_package": project.android_package,
            "ios_app_id": project.ios_app_id,
            "custom_scheme": project.custom_scheme,
            "custom_domain": project.custom_domain,
            "fallback_url": project.fallback_url,
            "is_active": project.is_active,
            "links_count": links_count,
            "total_clicks": total_clicks,
            "users_count": users_count,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        })
    
    return ApiResponse.success(
        data=projects_data,
        message="Projets récupérés avec succès"
    )

@router.get("/users")
async def get_admin_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None)
):
    """Récupérer tous les utilisateurs pour l'admin"""
    
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )
    
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    users_data = []
    for user in users:
        # Compter les liens créés
        links_count = db.query(DynamicLink).filter(DynamicLink.created_by == user.id).count()
        
        users_data.append({
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "links_count": links_count,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        })
    
    return ApiResponse.success(
        data={
            "users": users_data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        },
        message="Utilisateurs récupérés avec succès"
    )
