from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database import engine, Base
from app.api.v1 import sales, analytics, reports

# Criar tabelas no startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("🚀 QSDPharmalitics API iniciada!")
    print(f"📊 Documentação disponível em: http://localhost:8000/docs")
    yield
    # Shutdown
    print("👋 API finalizada!")

# Criar aplicação FastAPI
app = FastAPI(
    title="QSDPharmalitics API",
    description="API privada para estatísticas e análises farmacêuticas",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/")
async def root():
    return {
        "message": "QSDPharmalitics API v2.0",
        "status": "operational",
        "docs": "/docs",
        "version": "2.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# Incluir rotas da API
app.include_router(
    sales.router, 
    prefix="/api/v1/sales", 
    tags=["Sales"]
)

app.include_router(
    analytics.router, 
    prefix="/api/v1/analytics", 
    tags=["Analytics"]
)

app.include_router(
    reports.router, 
    prefix="/api/v1/reports", 
    tags=["Reports"]
)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return HTTPException(
        status_code=404,
        detail="Endpoint não encontrado"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )