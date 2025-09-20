import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, desc, case
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import numpy as np

from app.models.sales import Sale

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_sales_performance(
        self, 
        start_date: date, 
        end_date: date, 
        period: str = "month"
    ) -> List[Dict[str, Any]]:
        """Análise de performance de vendas por período"""
        
        # Definir o agrupamento baseado no período
        if period == "day":
            date_group = func.date(Sale.sale_date)
        elif period == "week":
            date_group = func.date_trunc('week', Sale.sale_date)
        elif period == "month":
            date_group = func.date_trunc('month', Sale.sale_date)
        elif period == "year":
            date_group = func.date_trunc('year', Sale.sale_date)
        else:
            date_group = func.date_trunc('month', Sale.sale_date)

        # Query principal
        results = self.db.query(
            date_group.label('period'),
            func.sum(Sale.total_price).label('revenue'),
            func.sum(Sale.quantity).label('quantity'),
            func.count(Sale.id).label('transactions'),
            func.avg(Sale.total_price).label('avg_order_value')
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            )
        ).group_by(date_group).order_by(date_group).all()

        return [
            {
                "period": str(result.period.date()) if hasattr(result.period, 'date') else str(result.period),
                "revenue": float(result.revenue or 0),
                "quantity": int(result.quantity or 0),
                "transactions": int(result.transactions or 0),
                "avg_order_value": float(result.avg_order_value or 0)
            }
            for result in results
        ]

    def get_performance_summary(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Resumo geral de performance"""
        
        summary = self.db.query(
            func.sum(Sale.total_price).label('total_revenue'),
            func.sum(Sale.quantity).label('total_quantity'),
            func.count(Sale.id).label('total_transactions'),
            func.avg(Sale.total_price).label('avg_order_value'),
            func.count(func.distinct(Sale.product_name)).label('unique_products'),
            func.count(func.distinct(Sale.pharmacy_name)).label('unique_pharmacies')
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            )
        ).first()

        return {
            "total_revenue": float(summary.total_revenue or 0),
            "total_quantity": int(summary.total_quantity or 0),
            "total_transactions": int(summary.total_transactions or 0),
            "avg_order_value": float(summary.avg_order_value or 0),
            "unique_products": int(summary.unique_products or 0),
            "unique_pharmacies": int(summary.unique_pharmacies or 0)
        }

    def get_market_share(
        self, 
        start_date: date, 
        end_date: date, 
        group_by: str = "category"
    ) -> List[Dict[str, Any]]:
        """Análise de market share"""
        
        # Definir campo de agrupamento
        group_field = {
            "product": Sale.product_name,
            "category": Sale.product_category,
            "pharmacy": Sale.pharmacy_name,
            "location": Sale.pharmacy_location
        }.get(group_by, Sale.product_category)

        # Query para market share
        results = self.db.query(
            group_field.label('segment'),
            func.sum(Sale.total_price).label('revenue'),
            func.sum(Sale.quantity).label('quantity'),
            func.count(Sale.id).label('transactions')
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True,
                group_field.isnot(None)
            )
        ).group_by(group_field).order_by(desc(func.sum(Sale.total_price))).all()

        # Calcular total para percentuais
        total_revenue = sum(result.revenue for result in results if result.revenue)
        
        return [
            {
                "segment": result.segment,
                "revenue": float(result.revenue or 0),
                "quantity": int(result.quantity or 0),
                "transactions": int(result.transactions or 0),
                "market_share_pct": round((result.revenue / total_revenue * 100), 2) if total_revenue > 0 else 0
            }
            for result in results
        ]

    def get_sales_trends(
        self, 
        start_date: date, 
        end_date: date, 
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Análise de tendências de vendas"""
        
        query = self.db.query(
            func.date(Sale.sale_date).label('date'),
            func.sum(Sale.total_price).label('revenue'),
            func.sum(Sale.quantity).label('quantity')
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            )
        )
        
        if category:
            query = query.filter(Sale.product_category.ilike(f"%{category}%"))
        
        results = query.group_by(func.date(Sale.sale_date)).order_by(func.date(Sale.sale_date)).all()

        return [
            {
                "date": str(result.date),
                "revenue": float(result.revenue or 0),
                "quantity": int(result.quantity or 0)
            }
            for result in results
        ]

    def get_top_products(
        self, 
        start_date: date, 
        end_date: date, 
        metric: str = "revenue",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Top produtos por métrica"""
        
        # Definir ordenação baseada na métrica
        if metric == "revenue":
            order_by = desc(func.sum(Sale.total_price))
        elif metric == "quantity":
            order_by = desc(func.sum(Sale.quantity))
        else:  # frequency
            order_by = desc(func.count(Sale.id))

        results = self.db.query(
            Sale.product_name,
            Sale.product_category,
            func.sum(Sale.total_price).label('revenue'),
            func.sum(Sale.quantity).label('quantity'),
            func.count(Sale.id).label('frequency'),
            func.avg(Sale.total_price).label('avg_order_value')
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            )
        ).group_by(
            Sale.product_name, 
            Sale.product_category
        ).order_by(order_by).limit(limit).all()

        return [
            {
                "product_name": result.product_name,
                "product_category": result.product_category,
                "revenue": float(result.revenue or 0),
                "quantity": int(result.quantity or 0),
                "frequency": int(result.frequency or 0),
                "avg_order_value": float(result.avg_order_value or 0)
            }
            for result in results
        ]

    def get_customer_analysis(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Análise de clientes/farmácias"""
        
        customers = self.db.query(
            Sale.pharmacy_name,
            func.sum(Sale.total_price).label('total_revenue'),
            func.sum(Sale.quantity).label('total_quantity'),
            func.count(Sale.id).label('total_orders'),
            func.avg(Sale.total_price).label('avg_order_value'),
            func.max(Sale.sale_date).label('last_order_date')
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True,
                Sale.pharmacy_name.isnot(None)
            )
        ).group_by(Sale.pharmacy_name).all()

        # Calcular segmentos
        revenues = [float(c.total_revenue or 0) for c in customers]
        
        if revenues:
            revenue_percentiles = np.percentile(revenues, [33, 66, 90])
            
            segments = {
                "high_value": len([r for r in revenues if r >= revenue_percentiles[2]]),
                "medium_value": len([r for r in revenues if revenue_percentiles[1] <= r < revenue_percentiles[2]]),
                "low_value": len([r for r in revenues if r < revenue_percentiles[1]])
            }
        else:
            segments = {"high_value": 0, "medium_value": 0, "low_value": 0}

        top_customers = [
            {
                "pharmacy_name": customer.pharmacy_name,
                "total_revenue": float(customer.total_revenue or 0),
                "total_quantity": int(customer.total_quantity or 0),
                "total_orders": int(customer.total_orders or 0),
                "avg_order_value": float(customer.avg_order_value or 0),
                "last_order_date": str(customer.last_order_date.date()) if customer.last_order_date else None
            }
            for customer in sorted(customers, key=lambda x: x.total_revenue or 0, reverse=True)
        ]

        return {
            "total_customers": len(customers),
            "segments": segments,
            "top_customers": top_customers,
            "avg_customer_value": np.mean(revenues) if revenues else 0
        }

    def get_revenue_analysis(
        self, 
        start_date: date, 
        end_date: date, 
        group_by: str = "month"
    ) -> List[Dict[str, Any]]:
        """Análise detalhada de receita"""
        
        # Definir agrupamento
        if group_by == "day":
            date_group = func.date(Sale.sale_date)
        elif group_by == "week":
            date_group = func.date_trunc('week', Sale.sale_date)
        elif group_by == "quarter":
            date_group = func.date_trunc('quarter', Sale.sale_date)
        else:  # month
            date_group = func.date_trunc('month', Sale.sale_date)

        results = self.db.query(
            date_group.label('period'),
            func.sum(Sale.total_price).label('revenue'),
            func.sum(Sale.quantity * Sale.unit_price).label('gross_revenue'),
            func.sum(Sale.discount).label('total_discount'),
            func.count(Sale.id).label('transactions')
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            )
        ).group_by(date_group).order_by(date_group).all()

        return [
            {
                "period": str(result.period.date()) if hasattr(result.period, 'date') else str(result.period),
                "revenue": float(result.revenue or 0),
                "gross_revenue": float(result.gross_revenue or 0),
                "total_discount": float(result.total_discount or 0),
                "transactions": int(result.transactions or 0),
                "discount_rate": round((result.total_discount / result.gross_revenue * 100), 2) if result.gross_revenue else 0
            }
            for result in results
        ]

    def calculate_growth_rate(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, float]:
        """Calcular taxa de crescimento"""
        
        period_length = (end_date - start_date).days
        mid_point = start_date + timedelta(days=period_length // 2)

        # Primeira metade
        first_half = self.db.query(
            func.sum(Sale.total_price)
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date < mid_point,
                Sale.is_active == True
            )
        ).scalar() or 0

        # Segunda metade
        second_half = self.db.query(
            func.sum(Sale.total_price)
        ).filter(
            and_(
                Sale.sale_date >= mid_point,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            )
        ).scalar() or 0

        growth_rate = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0

        return {
            "first_half_revenue": float(first_half),
            "second_half_revenue": float(second_half),
            "growth_rate_pct": round(growth_rate, 2)
        }

    def get_seasonality_analysis(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Análise de sazonalidade"""
        
        # Vendas por dia da semana
        weekday_sales = self.db.query(
            extract('dow', Sale.sale_date).label('weekday'),
            func.avg(Sale.total_price).label('avg_revenue')
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            )
        ).group_by(extract('dow', Sale.sale_date)).all()

        # Vendas por mês
        monthly_sales = self.db.query(
            extract('month', Sale.sale_date).label('month'),
            func.avg(Sale.total_price).label('avg_revenue')
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            )
        ).group_by(extract('month', Sale.sale_date)).all()

        weekdays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
        months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

        return {
            "by_weekday": [
                {
                    "weekday": weekdays[int(ws.weekday)],
                    "avg_revenue": float(ws.avg_revenue or 0)
                }
                for ws in weekday_sales
            ],
            "by_month": [
                {
                    "month": months[int(ms.month) - 1],
                    "avg_revenue": float(ms.avg_revenue or 0)
                }
                for ms in monthly_sales
            ]
        }

    def get_average_order_value(
        self, 
        start_date: date, 
        end_date: date
    ) -> float:
        """Calcular ticket médio"""
        
        avg_value = self.db.query(
            func.avg(Sale.total_price)
        ).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            )
        ).scalar()

        return float(avg_value or 0)

    def compare_periods(
        self, 
        current_summary: Dict[str, Any], 
        previous_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comparar dois períodos"""
        
        def calc_change(current: float, previous: float) -> Dict[str, Any]:
            if previous == 0:
                return {"value": current, "change_pct": 0, "direction": "neutral"}
            
            change_pct = ((current - previous) / previous) * 100
            direction = "up" if change_pct > 0 else "down" if change_pct < 0 else "neutral"
            
            return {
                "value": current,
                "change_pct": round(change_pct, 2),
                "direction": direction
            }

        return {
            "revenue": calc_change(
                current_summary.get("total_revenue", 0),
                previous_summary.get("total_revenue", 0)
            ),
            "transactions": calc_change(
                current_summary.get("total_transactions", 0),
                previous_summary.get("total_transactions", 0)
            ),
            "avg_order_value": calc_change(
                current_summary.get("avg_order_value", 0),
                previous_summary.get("avg_order_value", 0)
            )
        }