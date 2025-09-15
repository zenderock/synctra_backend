from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import time
import uvicorn

from app.middleware.rate_limit import RateLimitMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.api.sdk.v1.api import api_router as sdk_api_router
from app.api.v1.endpoints.redirect import router as redirect_router
from app.api.v1.endpoints.admin import router as admin_api_router
from app.api.v1.endpoints.admin_routes import router as admin_routes_router
from app.core.exceptions import SynctraException

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Synctra API",
    description="API pour la gestion des liens dynamiques et analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(RateLimitMiddleware)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field_name = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_name,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Données invalides",
            "details": errors
        }
    )

@app.exception_handler(SynctraException)
async def synctra_exception_handler(request: Request, exc: SynctraException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message, "details": exc.details}
    )

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routes API d'abord
app.include_router(api_router, prefix="/api/v1")
app.include_router(sdk_api_router, prefix="/sdk/v1")
app.include_router(admin_api_router, prefix="/api/v1/admin")

# Routes d'interface admin
app.include_router(admin_routes_router, prefix="/admin")

# Route de santé
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# Le router de redirection doit être en dernier pour éviter de capturer les autres routes
app.include_router(redirect_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
