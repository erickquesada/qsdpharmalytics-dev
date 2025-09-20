from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import hashlib
import json

from app.database import SessionLocal
from app.core.analytics import AnalyticsService

# Database Dependency
def get_db() -> Generator:
    """Dependency para obter sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Analytics Service Dependency
def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency para obter serviço de analytics"""
    return AnalyticsService(db)

# Date Range Dependency
def get_date_range(
    start_date: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)")
) -> tuple[date, date]:
    """
    Dependency para validar e padronizar range de datas
    Se não fornecidas, usa últimos 30 dias
    """
    if not end_date:
        end_date = date.today()
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Validações
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Data inicial deve ser anterior à data final"
        )
    
    # Limitar a 2 anos para performance
    max_range = timedelta(days=730)
    if (end_date - start_date) > max_range:
        raise HTTPException(
            status_code=400,
            detail="Período não pode ser superior a 2 anos"
        )
    
    return start_date, end_date

# Pagination Dependency
def get_pagination(
    skip: int = Query(0, ge=0, description="Registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros")
) -> dict:
    """Dependency para paginação"""
    return {"skip": skip, "limit": limit}

# Filter Dependency
def get_common_filters(
    product_name: Optional[str] = Query(None, description="Filtrar por nome do produto"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    pharmacy: Optional[str] = Query(None, description="Filtrar por farmácia"),
    sales_rep: Optional[str] = Query(None, description="Filtrar por representante")
) -> dict:
    """Dependency para filtros comuns"""
    filters = {}
    
    if product_name:
        filters["product_name"] = product_name.strip()
    
    if category:
        filters["category"] = category.strip()
    
    if pharmacy:
        filters["pharmacy"] = pharmacy.strip()
    
    if sales_rep:
        filters["sales_rep"] = sales_rep.strip()
    
    return filters

# Cache Key Generator
def generate_cache_key(
    endpoint: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    **params
) -> str:
    """Gerar chave única para cache"""
    
    cache_data = {
        "endpoint": endpoint,
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None,
        "params": params
    }
    
    # Serializar e criar hash
    cache_string = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()

# Cache Dependency
def get_cache_info(
    endpoint: str,
    date_range: tuple[date, date] = Depends(get_date_range),
    **kwargs
) -> dict:
    """Dependency para informações de cache"""
    start_date, end_date = date_range
    
    return {
        "cache_key": generate_cache_key(endpoint, start_date, end_date, **kwargs),
        "start_date": start_date,
        "end_date": end_date,
        "endpoint": endpoint
    }

# Validation Dependencies
def validate_period(
    period: str = Query("month", regex="^(day|week|month|quarter|year)$")
) -> str:
    """Validar período para agrupamento"""
    return period

def validate_metric(
    metric: str = Query("revenue", regex="^(revenue|quantity|frequency)$")
) -> str:
    """Validar métrica para ranking"""
    return metric

def validate_group_by(
    group_by: str = Query("category", regex="^(product|category|pharmacy|location|sales_rep)$")
) -> str:
    """Validar campo de agrupamento"""
    return group_by

def validate_format(
    format: str = Query("json", regex="^(json|csv|excel|pdf)$")
) -> str:
    """Validar formato de export"""
    return format

# Rate Limiting Dependency (futuro)
def rate_limit_check(
    endpoint: str = "default",
    max_requests: int = 100,
    window_minutes: int = 60
) -> bool:
    """
    Dependency para rate limiting (implementação futura)
    Por enquanto sempre retorna True
    """
    # TODO: Implementar rate limiting com Redis
    return True

# Error Handler Dependency
def handle_analytics_errors(func):
    """Decorator para tratar erros de analytics"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erro nos parâmetros: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno: {str(e)}"
            )
    return wrapper

# Response Metadata
def get_response_metadata(
    start_date: date,
    end_date: date,
    total_records: Optional[int] = None,
    cache_hit: bool = False
) -> dict:
    """Gerar metadata para responses"""
    return {
        "period": f"{start_date} to {end_date}",
        "days_range": (end_date - start_date).days,
        "total_records": total_records,
        "cache_hit": cache_hit,
        "generated_at": datetime.now().isoformat(),
        "timezone": "America/Sao_Paulo"
    }

# Performance Monitoring
class PerformanceMonitor:
    """Context manager para monitorar performance de endpoints"""
    
    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            # TODO: Log performance metrics
            print(f"Endpoint {self.endpoint_name} executado em {duration:.3f}s")

def get_performance_monitor(endpoint: str):
    """Dependency para monitoramento de performance"""
    return PerformanceMonitor(endpoint)

# Business Logic Validations
def validate_business_rules(
    start_date: date,
    end_date: date,
    **params
) -> dict:
    """Validações específicas de regras de negócio"""
    
    # Não permitir consultas muito antigas (performance)
    if start_date < date.today() - timedelta(days=1095):  # 3 anos
        raise HTTPException(
            status_code=400,
            detail="Consultas limitadas aos últimos 3 anos"
        )
    
    # Alertar sobre períodos muito longos
    warning = None
    if (end_date - start_date).days > 365:
        warning = "Período longo pode impactar performance"
    
    return {
        "validated": True,
        "warning": warning,
        "business_rules_applied": [
            "max_historical_data_3_years",
            "performance_warning_1_year"
        ]
    }

# Advanced Filters
def get_advanced_filters(
    min_revenue: Optional[float] = Query(None, description="Receita mínima"),
    max_revenue: Optional[float] = Query(None, description="Receita máxima"),
    min_quantity: Optional[int] = Query(None, description="Quantidade mínima"),
    customer_type: Optional[str] = Query(None, description="Tipo de cliente"),
    payment_method: Optional[str] = Query(None, description="Forma de pagamento"),
    campaign_id: Optional[str] = Query(None, description="ID da campanha")
) -> dict:
    """Filtros avançados para queries complexas"""
    
    filters = {}
    
    if min_revenue is not None:
        filters["min_revenue"] = min_revenue
    
    if max_revenue is not None:
        filters["max_revenue"] = max_revenue
        
    if min_quantity is not None:
        filters["min_quantity"] = min_quantity
    
    if customer_type:
        filters["customer_type"] = customer_type.strip().lower()
    
    if payment_method:
        filters["payment_method"] = payment_method.strip().lower()
    
    if campaign_id:
        filters["campaign_id"] = campaign_id.strip()
    
    return filters