from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.database.base import Base, engine
from backend.api.v1 import api_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting QSDPharmalitics API v2.0...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("📊 Database tables created successfully")
    
    # Initialize cache connections, background tasks, etc.
    logger.info("✅ QSDPharmalitics API is ready!")
    logger.info(f"📚 Documentation available at: http://localhost:8001{settings.API_V1_STR}/docs")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down QSDPharmalitics API...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="🏥 Advanced Pharmaceutical Analytics & Reporting Platform",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Root endpoint
@app.get("/")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def root(request: Request):
    return {
        "message": "🏥 QSDPharmalitics API v2.0",
        "description": "Advanced Pharmaceutical Analytics & Reporting Platform",
        "status": "operational",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "api_v1": settings.API_V1_STR,
        "environment": settings.ENVIRONMENT
    }


# Health check endpoint
@app.get(f"{settings.API_V1_STR}/health")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def health_check(request: Request):
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": time.time(),
        "environment": settings.ENVIRONMENT,
        "database": "connected",
        "analytics": "enabled" if settings.ENABLE_ADVANCED_ANALYTICS else "basic"
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Global exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested endpoint does not exist",
            "path": str(request.url.path),
            "method": request.method
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


# Startup event for additional initialization
@app.on_event("startup")
async def startup_event():
    logger.info("🔧 Performing additional startup tasks...")
    # Add any additional startup logic here
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )