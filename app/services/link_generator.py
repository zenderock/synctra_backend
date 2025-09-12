import secrets
import string
from typing import Optional
from sqlalchemy.orm import Session

from app.models.dynamic_link import DynamicLink

class LinkGenerator:
    @staticmethod
    def generate_short_code(length: int = 8) -> str:
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    def generate_unique_short_code(db: Session, length: int = 8) -> str:
        max_attempts = 10
        for _ in range(max_attempts):
            short_code = LinkGenerator.generate_short_code(length)
            existing = db.query(DynamicLink).filter(
                DynamicLink.short_code == short_code
            ).first()
            if not existing:
                return short_code
        
        return LinkGenerator.generate_short_code(length + 2)
    
    @staticmethod
    def build_short_url(short_code: str, domain: str) -> str:
        return f"https://{domain}/{short_code}"
    
    @staticmethod
    def build_utm_url(original_url: str, utm_params: dict) -> str:
        if not utm_params:
            return original_url
        
        separator = "&" if "?" in original_url else "?"
        utm_string = "&".join([f"{key}={value}" for key, value in utm_params.items() if value])
        
        if utm_string:
            return f"{original_url}{separator}{utm_string}"
        return original_url
