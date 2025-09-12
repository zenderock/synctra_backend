from fastapi import Request, HTTPException, status
from typing import Dict, Optional
import time
import redis
from app.core.database import get_redis
from app.core.config import settings

class RateLimiter:
    def __init__(self):
        self.redis_client = get_redis()
    
    def check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        identifier: str = "global"
    ) -> bool:
        current_time = int(time.time())
        window_start = current_time - window
        
        pipe = self.redis_client.pipeline()
        
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {identifier: current_time})
        pipe.expire(key, window)
        
        results = pipe.execute()
        current_requests = results[1]
        
        return current_requests < limit
    
    def get_api_key_limit(self, request: Request) -> Optional[str]:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            key = f"rate_limit:api:{api_key}"
            if not self.check_rate_limit(
                key, 
                settings.RATE_LIMIT_PER_HOUR, 
                3600, 
                str(int(time.time()))
            ):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Limite de taux API dépassée"
                )
        return api_key
    
    def check_ip_limit(self, request: Request):
        client_ip = request.client.host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        key = f"rate_limit:ip:{client_ip}"
        if not self.check_rate_limit(
            key, 
            settings.RATE_LIMIT_PER_SECOND * 60, 
            60, 
            str(int(time.time()))
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Limite de taux IP dépassée"
            )

rate_limiter = RateLimiter()
