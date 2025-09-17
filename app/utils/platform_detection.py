import re
from typing import Dict, Optional
from user_agents import parse


def detect_platform_from_user_agent(user_agent: str) -> Dict[str, Optional[str]]:
    """
    Détecte la plateforme, le navigateur, l'OS et le type d'appareil à partir du User-Agent
    """
    if not user_agent:
        return {
            "platform": "unknown",
            "device_type": "unknown",
            "browser": "unknown",
            "os": "unknown"
        }
    
    ua = parse(user_agent)
    
    # Détection de la plateforme
    platform = "web"
    if ua.is_mobile:
        if "Android" in user_agent:
            platform = "android"
        elif "iPhone" in user_agent or "iPad" in user_agent:
            platform = "ios"
    elif ua.is_pc:
        if "Windows" in user_agent:
            platform = "windows"
        elif "Macintosh" in user_agent or "Mac OS" in user_agent:
            platform = "macos"
        elif "Linux" in user_agent:
            platform = "linux"
    
    # Type d'appareil
    device_type = "desktop"
    if ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    
    return {
        "platform": platform,
        "device_type": device_type,
        "browser": ua.browser.family if ua.browser.family else "unknown",
        "os": ua.os.family if ua.os.family else "unknown"
    }


def should_redirect_to_app_store(user_agent: str, android_package: str = None, ios_bundle_id: str = None) -> tuple[bool, str]:
    """
    Détermine si on doit rediriger vers l'app store et retourne l'URL appropriée
    """
    detection = detect_platform_from_user_agent(user_agent)
    
    if detection["platform"] == "android" and android_package:
        return True, f"https://play.google.com/store/apps/details?id={android_package}"
    elif detection["platform"] == "ios" and ios_bundle_id:
        return True, f"https://apps.apple.com/app/id{ios_bundle_id}"
    
    return False, ""


def get_fallback_url(user_agent: str, android_fallback: str = None, ios_fallback: str = None, desktop_fallback: str = None) -> str:
    """
    Retourne l'URL de fallback appropriée selon la plateforme
    """
    detection = detect_platform_from_user_agent(user_agent)
    
    if detection["platform"] == "android" and android_fallback:
        return android_fallback
    elif detection["platform"] == "ios" and ios_fallback:
        return ios_fallback
    elif detection["device_type"] == "desktop" and desktop_fallback:
        return desktop_fallback
    
    return ""
