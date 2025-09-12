import re
from typing import Dict, Optional

class PlatformDetector:
    @staticmethod
    def detect_platform(user_agent: str) -> Dict[str, str]:
        user_agent = user_agent.lower()
        
        platform = "web"
        device_type = "desktop"
        browser = "unknown"
        os = "unknown"
        
        if re.search(r'android', user_agent):
            platform = "android"
            os = "Android"
            device_type = "mobile"
        elif re.search(r'iphone|ipad', user_agent):
            platform = "ios"
            os = "iOS"
            device_type = "mobile" if "iphone" in user_agent else "tablet"
        elif re.search(r'windows nt', user_agent):
            platform = "windows"
            os = "Windows"
        elif re.search(r'macintosh|mac os x', user_agent):
            platform = "macos"
            os = "macOS"
        elif re.search(r'linux', user_agent):
            platform = "linux"
            os = "Linux"
        
        if re.search(r'chrome', user_agent):
            browser = "Chrome"
        elif re.search(r'firefox', user_agent):
            browser = "Firefox"
        elif re.search(r'safari', user_agent):
            browser = "Safari"
        elif re.search(r'edge', user_agent):
            browser = "Edge"
        
        if re.search(r'mobile|phone', user_agent) and device_type == "desktop":
            device_type = "mobile"
        elif re.search(r'tablet|ipad', user_agent):
            device_type = "tablet"
        
        return {
            "platform": platform,
            "device_type": device_type,
            "browser": browser,
            "os": os
        }
    
    @staticmethod
    def get_redirect_url(
        link_data: Dict,
        platform_info: Dict[str, str]
    ) -> str:
        platform = platform_info["platform"]
        
        if platform == "android" and link_data.get("android_package"):
            if link_data.get("android_fallback_url"):
                return link_data["android_fallback_url"]
        elif platform == "ios" and link_data.get("ios_bundle_id"):
            if link_data.get("ios_fallback_url"):
                return link_data["ios_fallback_url"]
        elif platform in ["windows", "macos", "linux"] and link_data.get("desktop_fallback_url"):
            return link_data["desktop_fallback_url"]
        
        return link_data["original_url"]
