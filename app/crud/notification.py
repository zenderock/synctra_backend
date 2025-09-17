from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.crud.base import CRUDBase
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate


class CRUDNotification(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):
    def get_by_user(
        self, 
        db: Session, 
        *, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Notification]:
        query = db.query(self.model).filter(self.model.user_id == user_id)
        
        if unread_only:
            query = query.filter(self.model.read == False)
            
        return query.order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()

    def get_unread_count(self, db: Session, *, user_id: str) -> int:
        return db.query(self.model).filter(
            and_(self.model.user_id == user_id, self.model.read == False)
        ).count()

    def mark_as_read(self, db: Session, *, notification_id: str, user_id: str) -> Optional[Notification]:
        notification = db.query(self.model).filter(
            and_(self.model.id == notification_id, self.model.user_id == user_id)
        ).first()
        
        if notification and not notification.read:
            notification.read = True
            from datetime import datetime
            notification.read_at = datetime.utcnow()
            db.commit()
            db.refresh(notification)
            
        return notification

    def mark_all_as_read(self, db: Session, *, user_id: str) -> int:
        from datetime import datetime
        
        updated_count = db.query(self.model).filter(
            and_(self.model.user_id == user_id, self.model.read == False)
        ).update({
            "read": True,
            "read_at": datetime.utcnow()
        })
        
        db.commit()
        return updated_count

    def delete_by_user(self, db: Session, *, notification_id: str, user_id: str) -> bool:
        notification = db.query(self.model).filter(
            and_(self.model.id == notification_id, self.model.user_id == user_id)
        ).first()
        
        if notification:
            db.delete(notification)
            db.commit()
            return True
        return False

    def create_system_notification(
        self, 
        db: Session, 
        *, 
        user_id: str, 
        title: str, 
        message: str, 
        notification_type: str = "info",
        category: str = "system",
        action_url: Optional[str] = None
    ) -> Notification:
        notification_data = NotificationCreate(
            user_id=user_id,
            type=notification_type,
            category=category,
            title=title,
            message=message,
            action_url=action_url
        )
        return self.create(db=db, obj_in=notification_data)


notification = CRUDNotification(Notification)
