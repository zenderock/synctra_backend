from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.rate_limiter import rate_limiter

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            rate_limiter.get_api_key_limit(request)
        
        if request.url.path not in ["/health", "/api/docs", "/api/redoc"]:
            rate_limiter.check_ip_limit(request)
        
        response = await call_next(request)
        return response
