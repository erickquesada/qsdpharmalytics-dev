from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import pandas as pd

from app.database import get_db
from app.models.sales import Sale
from app.core.analytics import AnalyticsService

router = APIRouter()

# ========== ANALYTICS ENDPOINTS ==========

@router.get("/sales-performance")
async def sales_performance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = Query("month", regex="^(day|week|month|year)$"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Análise de performance de vendas
    - Vendas totais por período
    - Crescimento percentual
    - Produtos top performers
    """
    analytics = AnalyticsService(db)
    
    # Definir período padrão se não fornecido
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Performance geral
    performance = analytics.get_sales_performance(start_date, end_date, period)
    
    return {
        "period": f"{start_date} to {end_date}",
        "grouping": period,
        "performance": performance,
        "summary": analytics.get_performance_summary(start_date, end_date)
    }

@router.get("/market-share")
async def market_share(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    group_by: str = Query("category", regex="^(product|category|pharmacy|location)$"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Análise de market share
    - Participação por produto/categoria/farmácia
    - Comparativo de períodos
    """
    analytics = AnalyticsService(db)
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    market_share = analytics.get_market_share(start_date, end_date, group_by)
    
    return {
        "period": f"{start_date} to {end_date}",
        "group_by": group_by,
        "market_share": market_share,
        "top_performers": market_share[:5] if market_share else []
    }

@router.get("/trends")
async def sales_trends(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product_category: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Análise de tendências temporais
    - Crescimento ao longo do tempo
    - Sazonalidade
    - Previsões simples
    """
    analytics = AnalyticsService(db)
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    
    trends = analytics.get_sales_trends(start_date, end_date, product_category)
    
    return {
        "period": f"{start_date} to {end_date}",
        "category_filter": product_category,
        "trends": trends,
        "growth_rate": analytics.calculate_growth_rate(start_date, end_date),
        "seasonality": analytics.get_seasonality_analysis(start_date, end_date)
    }

@router.get("/top-products")
async def top_products(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    metric: str = Query("revenue", regex="^(revenue|quantity|frequency)$"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Produtos mais vendidos
    - Por receita, quantidade ou frequência
    - Rankings e comparativos
    """
    analytics = AnalyticsService(db)
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    top_products = analytics.get_top_products(start_date, end_date, metric, limit)
    
    return {
        "period": f"{start_date} to {end_date}",
        "metric": metric,
        "limit": limit,
        "top_products": top_products
    }

@router.get("/customer-analysis")
async def customer_analysis(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Análise de clientes/farmácias
    - Valor por cliente
    - Frequência de compras
    - Segmentação
    """
    analytics = AnalyticsService(db)
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    customer_analysis = analytics.get_customer_analysis(start_date, end_date)
    
    return {
        "period": f"{start_date} to {end_date}",
        "customer_metrics": customer_analysis,
        "top_customers": customer_analysis.get("top_customers", [])[:10],
        "customer_segments": customer_analysis.get("segments", {})
    }

@router.get("/revenue-analysis")
async def revenue_analysis(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    group_by: str = Query("month", regex="^(day|week|month|quarter)$"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Análise detalhada de receita
    - Receita por período
    - Margem de lucro
    - Comparativos
    """
    analytics = AnalyticsService(db)
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    
    revenue_analysis = analytics.get_revenue_analysis(start_date, end_date, group_by)
    
    return {
        "period": f"{start_date} to {end_date}",
        "grouping": group_by,
        "revenue_data": revenue_analysis,
        "total_revenue": sum(item.get("revenue", 0) for item in revenue_analysis),
        "average_order_value": analytics.get_average_order_value(start_date, end_date)
    }

@router.get("/dashboard-summary")
async def dashboard_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Resumo para dashboard principal
    - KPIs principais
    - Métricas rápidas
    - Comparativos de período
    """
    analytics = AnalyticsService(db)
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Período anterior para comparação
    previous_start = start_date - (end_date - start_date)
    previous_end = start_date
    
    current_summary = analytics.get_performance_summary(start_date, end_date)
    previous_summary = analytics.get_performance_summary(previous_start, previous_end)
    
    return {
        "current_period": {
            "start": start_date,
            "end": end_date,
            "summary": current_summary
        },
        "previous_period": {
            "start": previous_start,
            "end": previous_end,
            "summary": previous_summary
        },
        "comparisons": analytics.compare_periods(
            current_summary, previous_summary
        ),
        "top_products": analytics.get_top_products(start_date, end_date, "revenue", 5),
        "recent_trends": analytics.get_sales_trends(start_date, end_date)[-7:]  # Últimos 7 pontos
    }