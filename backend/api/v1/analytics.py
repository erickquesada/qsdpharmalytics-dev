from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import pandas as pd

from backend.database.base import get_db
from backend.api.dependencies import get_current_active_user, get_analyst_or_admin_user
from backend.schemas.analytics import (
    SalesPerformanceResponse, 
    MarketShareResponse, 
    TrendAnalysisResponse, 
    DashboardSummaryResponse,
    AnalyticsFilters
)
from backend.models.sales import Sale
from backend.models.products import Product, ProductCategory
from backend.models.pharmacies import Pharmacy
from backend.models.user import User

router = APIRouter()


@router.get("/sales-performance", response_model=SalesPerformanceResponse)
async def get_sales_performance(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"), 
    period: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly)$"),
    compare_previous: bool = Query(True, description="Compare with previous period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_analyst_or_admin_user)
):
    """Get sales performance analytics"""
    
    # Set default date range if not provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        if period == "daily":
            start_date = end_date - timedelta(days=30)
        elif period == "weekly":
            start_date = end_date - timedelta(weeks=12)
        elif period == "monthly":
            start_date = end_date - timedelta(days=365)
        else:  # quarterly
            start_date = end_date - timedelta(days=730)
    
    # Base query
    query = db.query(Sale).filter(
        Sale.is_active == True,
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    )
    
    sales = query.all()
    
    if not sales:
        return SalesPerformanceResponse(
            period=period,
            data_points=[],
            total_revenue=Decimal(0),
            revenue_growth=None,
            top_products=[],
            top_pharmacies=[]
        )
    
    # Create DataFrame for analysis
    df = pd.DataFrame([
        {
            'sale_date': sale.sale_date,
            'revenue': float(sale.final_amount),
            'quantity': sale.quantity,
            'product_id': sale.product_id,
            'pharmacy_id': sale.pharmacy_id
        }
        for sale in sales
    ])
    
    # Group by period
    df['period_key'] = pd.to_datetime(df['sale_date'])
    
    if period == "daily":
        df['period_key'] = df['period_key'].dt.date
    elif period == "weekly":
        df['period_key'] = df['period_key'].dt.to_period('W').dt.start_time.dt.date
    elif period == "monthly":
        df['period_key'] = df['period_key'].dt.to_period('M').dt.start_time.dt.date
    else:  # quarterly
        df['period_key'] = df['period_key'].dt.to_period('Q').dt.start_time.dt.date
    
    # Aggregate by period
    period_data = df.groupby('period_key').agg({
        'revenue': 'sum',
        'quantity': 'sum',
        'product_id': 'count'
    }).reset_index()
    
    period_data.columns = ['period', 'revenue', 'quantity', 'orders']
    
    # Convert to data points
    data_points = [
        {
            'period': str(row['period']),
            'revenue': float(row['revenue']),
            'quantity': int(row['quantity']),
            'orders': int(row['orders']),
            'average_order_value': float(row['revenue'] / row['orders']) if row['orders'] > 0 else 0
        }
        for _, row in period_data.iterrows()
    ]
    
    total_revenue = Decimal(str(df['revenue'].sum()))
    
    # Calculate growth if comparison is requested
    revenue_growth = None
    if compare_previous and len(period_data) > 1:
        recent_revenue = period_data['revenue'].iloc[-1]
        previous_revenue = period_data['revenue'].iloc[-2]
        if previous_revenue > 0:
            revenue_growth = Decimal(str(((recent_revenue - previous_revenue) / previous_revenue) * 100))
    
    # Get top products
    top_products_query = db.query(
        Product.name,
        Product.code,
        func.sum(Sale.final_amount).label('revenue'),
        func.sum(Sale.quantity).label('quantity')
    ).join(Sale.product)\
     .filter(
         Sale.is_active == True,
         Sale.sale_date >= start_date,
         Sale.sale_date <= end_date
     )\
     .group_by(Product.id, Product.name, Product.code)\
     .order_by(desc('revenue'))\
     .limit(5)\
     .all()
    
    top_products = [
        {
            'name': product.name,
            'code': product.code,
            'revenue': float(product.revenue),
            'quantity': int(product.quantity)
        }
        for product in top_products_query
    ]
    
    # Get top pharmacies
    top_pharmacies_query = db.query(
        Pharmacy.name,
        Pharmacy.city,
        func.sum(Sale.final_amount).label('revenue'),
        func.count(Sale.id).label('orders')
    ).join(Sale.pharmacy)\
     .filter(
         Sale.is_active == True,
         Sale.sale_date >= start_date,
         Sale.sale_date <= end_date
     )\
     .group_by(Pharmacy.id, Pharmacy.name, Pharmacy.city)\
     .order_by(desc('revenue'))\
     .limit(5)\
     .all()
    
    top_pharmacies = [
        {
            'name': pharmacy.name,
            'location': pharmacy.city,
            'revenue': float(pharmacy.revenue),
            'orders': int(pharmacy.orders)
        }
        for pharmacy in top_pharmacies_query
    ]
    
    return SalesPerformanceResponse(
        period=period,
        data_points=data_points,
        total_revenue=total_revenue,
        revenue_growth=revenue_growth,
        top_products=top_products,
        top_pharmacies=top_pharmacies
    )


@router.get("/market-share")
async def get_market_share_analysis(
    category: Optional[str] = Query(None, description="Product category"),
    region: Optional[str] = Query(None, description="Geographic region"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_analyst_or_admin_user)
):
    """Get market share analysis"""
    
    # Set default date range
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    
    # This would typically integrate with external market data
    # For now, we'll provide internal analysis
    
    query = db.query(
        ProductCategory.name,
        func.sum(Sale.final_amount).label('our_revenue'),
        func.count(Sale.id).label('our_orders')
    ).join(Sale.product).join(Product.category)\
     .filter(
         Sale.is_active == True,
         Sale.sale_date >= start_date,
         Sale.sale_date <= end_date
     )
    
    if category:
        query = query.filter(ProductCategory.name.ilike(f"%{category}%"))
    
    if region:
        query = query.filter(Sale.region.ilike(f"%{region}%"))
    
    results = query.group_by(ProductCategory.name)\
        .order_by(desc('our_revenue'))\
        .all()
    
    market_data = []
    for result in results:
        # Simulate market size (in real implementation, this would come from external data)
        estimated_market_size = float(result.our_revenue) * 2.5  # Assume we have 40% market share
        
        market_data.append(MarketShareResponse(
            category=result.name,
            our_revenue=Decimal(str(result.our_revenue)),
            total_market_size=Decimal(str(estimated_market_size)),
            market_share_percentage=Decimal("40.0"),  # Simulated
            market_rank=1,  # Simulated
            competitor_count=5,  # Simulated
            trend_direction="increasing"  # Simulated
        ))
    
    return market_data


@router.get("/dashboard-summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard summary with key metrics"""
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)
    
    # Current period metrics
    current_sales = db.query(Sale).filter(
        Sale.is_active == True,
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).all()
    
    # Previous period metrics
    previous_sales = db.query(Sale).filter(
        Sale.is_active == True,
        Sale.sale_date >= previous_start,
        Sale.sale_date < start_date
    ).all()
    
    # Calculate metrics
    current_revenue = sum(sale.final_amount for sale in current_sales)
    previous_revenue = sum(sale.final_amount for sale in previous_sales)
    revenue_growth = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else Decimal(0)
    
    current_orders = len(current_sales)
    previous_orders = len(previous_sales)
    orders_growth = ((current_orders - previous_orders) / previous_orders * 100) if previous_orders > 0 else Decimal(0)
    
    # Active pharmacies
    active_pharmacies = db.query(Pharmacy).filter(Pharmacy.is_active == True).count()
    
    # Top products (last 30 days)
    top_products_query = db.query(
        Product.name,
        func.sum(Sale.final_amount).label('revenue')
    ).join(Sale.product)\
     .filter(
         Sale.is_active == True,
         Sale.sale_date >= start_date
     )\
     .group_by(Product.id, Product.name)\
     .order_by(desc('revenue'))\
     .limit(5)\
     .all()
    
    top_products = [
        {'name': p.name, 'revenue': float(p.revenue)}
        for p in top_products_query
    ]
    
    # Recent sales
    recent_sales_query = db.query(Sale)\
        .filter(Sale.is_active == True)\
        .order_by(desc(Sale.created_at))\
        .limit(10)\
        .all()
    
    recent_sales = [
        {
            'id': sale.id,
            'amount': float(sale.final_amount),
            'date': sale.sale_date.isoformat(),
            'status': sale.status.value
        }
        for sale in recent_sales_query
    ]
    
    # Monthly trend (last 6 months)
    six_months_ago = end_date - timedelta(days=180)
    # Use strftime for SQLite compatibility (works with both SQLite and PostgreSQL)
    monthly_sales = db.query(
        func.strftime('%Y-%m', Sale.sale_date).label('month'),
        func.sum(Sale.final_amount).label('revenue')
    ).filter(
        Sale.is_active == True,
        Sale.sale_date >= six_months_ago
    ).group_by(func.strftime('%Y-%m', Sale.sale_date))\
     .order_by('month')\
     .all()
    
    monthly_trend = [
        {
            'month': month.month,
            'revenue': float(month.revenue)
        }
        for month in monthly_sales
    ]
    
    # Generate alerts
    alerts = []
    if revenue_growth < -10:
        alerts.append("Revenue declined by more than 10% compared to previous period")
    if current_orders < previous_orders * 0.8:
        alerts.append("Order volume is significantly lower than previous period")
    
    return DashboardSummaryResponse(
        total_revenue=Decimal(str(current_revenue)),
        revenue_growth=Decimal(str(revenue_growth)),
        total_orders=current_orders,
        orders_growth=Decimal(str(orders_growth)),
        active_pharmacies=active_pharmacies,
        top_products=top_products,
        recent_sales=recent_sales,
        monthly_trend=monthly_trend,
        alerts=alerts
    )


@router.get("/trends")
async def get_trend_analysis(
    metric: str = Query("revenue", regex="^(revenue|orders|customers)$"),
    period: str = Query("monthly", regex="^(daily|weekly|monthly)$"),
    forecast_periods: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_analyst_or_admin_user)
):
    """Get trend analysis and forecasting"""
    
    # This is a simplified implementation
    # In production, you'd use more sophisticated forecasting models
    
    end_date = date.today()
    if period == "daily":
        start_date = end_date - timedelta(days=90)
    elif period == "weekly":
        start_date = end_date - timedelta(weeks=52)
    else:  # monthly
        start_date = end_date - timedelta(days=365)
    
    # Get historical data
    sales = db.query(Sale).filter(
        Sale.is_active == True,
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).all()
    
    if not sales:
        return {
            "analysis_name": f"{metric.title()} Trend Analysis",
            "trend_direction": "stable",
            "trend_strength": Decimal("0.0"),
            "seasonal_pattern": False,
            "forecast_data": None,
            "analysis_period": period
        }
    
    # Create DataFrame for analysis
    df = pd.DataFrame([
        {
            'date': sale.sale_date,
            'revenue': float(sale.final_amount),
            'orders': 1
        }
        for sale in sales
    ])
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    # Resample by period
    if period == "daily":
        df_resampled = df.resample('D').sum()
    elif period == "weekly":
        df_resampled = df.resample('W').sum()
    else:  # monthly
        df_resampled = df.resample('M').sum()
    
    # Simple trend analysis
    values = df_resampled[metric].values
    if len(values) > 2:
        # Calculate simple linear trend
        x = range(len(values))
        slope = (values[-1] - values[0]) / (len(values) - 1)
        
        trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        trend_strength = abs(slope) / (sum(values) / len(values)) if sum(values) > 0 else 0
    else:
        trend_direction = "stable"
        trend_strength = 0
    
    # Simple forecasting (just extends the trend)
    forecast_data = []
    if len(values) > 0:
        last_value = values[-1]
        for i in range(1, forecast_periods + 1):
            forecasted_value = last_value + (slope * i)
            forecast_data.append({
                'period': i,
                'forecasted_value': max(0, forecasted_value)  # Ensure non-negative
            })
    
    return {
        "analysis_name": f"{metric.title()} Trend Analysis",
        "trend_direction": trend_direction,
        "trend_strength": Decimal(str(trend_strength)),
        "seasonal_pattern": False,  # Simplified - would need more sophisticated analysis
        "forecast_data": forecast_data,
        "analysis_period": period
    }