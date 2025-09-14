from sqlalchemy.orm import Session
from app.models.link_click import LinkClick
from datetime import datetime
from typing import Optional

class AnalyticsService:
    @staticmethod
    async def record_click(
        db: Session,
        link_id: int,
        ip_address: str,
        user_agent: str,
        referer: Optional[str] = None,
        country: Optional[str] = None,
        device_type: Optional[str] = None,
        os: Optional[str] = None,
        browser: Optional[str] = None
    ):
        """Enregistrer un clic sur un lien pour les analytics."""
        
        click = LinkClick(
            link_id=link_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            country=country,
            device_type=device_type,
            os=os,
            browser=browser,
            clicked_at=datetime.utcnow()
        )
        
        db.add(click)
        db.commit()
        db.refresh(click)
        
        return click
    
    @staticmethod
    def get_link_stats(db: Session, link_id: int):
        """Récupérer les statistiques d'un lien."""
        
        total_clicks = db.query(LinkClick).filter(
            LinkClick.link_id == link_id
        ).count()
        
        unique_clicks = db.query(LinkClick.ip_address).filter(
            LinkClick.link_id == link_id
        ).distinct().count()
        
        return {
            "total_clicks": total_clicks,
            "unique_clicks": unique_clicks
        }
    
    @staticmethod
    def get_project_stats(db: Session, project_id: int):
        """Récupérer les statistiques d'un projet."""
        
        from app.models.dynamic_link import DynamicLink
        
        # Récupérer tous les liens du projet
        project_links = db.query(DynamicLink.id).filter(
            DynamicLink.project_id == project_id
        ).subquery()
        
        total_clicks = db.query(LinkClick).filter(
            LinkClick.link_id.in_(project_links)
        ).count()
        
        unique_clicks = db.query(LinkClick.ip_address).filter(
            LinkClick.link_id.in_(project_links)
        ).distinct().count()
        
        return {
            "total_clicks": total_clicks,
            "unique_clicks": unique_clicks
        }
