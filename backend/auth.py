"""Authentication middleware for Jakebot Dashboard"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from .config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Bearer token authentication middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth if disabled
        if not settings.auth_enabled:
            return await call_next(request)
        
        # Skip auth for health check endpoints
        if request.url.path in ["/health", "/api/system/status"]:
            return await call_next(request)
        
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header"
            )
        
        token = auth_header.replace("Bearer ", "")
        if token != settings.auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return await call_next(request)
