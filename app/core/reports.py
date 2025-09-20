import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import io
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart

from app.models.sales import Sale
from app.core.analytics import AnalyticsService

class ReportsService:
    """Serviço para geração de relatórios"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analytics = AnalyticsService(db)
    
    def generate_executive_summary(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Gerar resumo executivo completo"""
        
        # Período anterior para comparação
        period_length = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_length)
        prev_end = start_date - timedelta(days=1)
        
        # Dados do período atual
        current_summary = self.analytics.get_performance_summary(start_date, end_date)
        current_trends = self.analytics.get_sales_trends(start_date, end_date)
        top_products = self.analytics.get_top_products(start_date, end_date, "revenue", 10)
        market_share = self.analytics.get_market_share(start_date, end_date, "category")
        customer_analysis = self.analytics.get_customer_analysis(start_date, end_date)
        
        # Dados do período anterior
        prev_summary = self.analytics.get_performance_summary(prev_start, prev_end)
        
        # Comparações
        comparisons = self.analytics.compare_periods(current_summary, prev_summary)
        
        # KPIs principais
        kpis = self._calculate_key_kpis(current_summary, comparisons)
        
        # Insights automáticos
        insights = self._generate_insights(
            current_summary, prev_summary, top_products, market_share
        )
        
        return {
            "period": {
                "current": f"{start_date} to {end_date}",
                "previous": f"{prev_start} to {prev_end}"
            },
            "kpis": kpis,
            "summary": current_summary,
            "comparisons": comparisons,
            "trends": current_trends[-30:] if current_trends else [],  # Últimos 30 pontos
            "top_products": top_products[:5],
            "market_share": market_share[:5],
            "customer_insights": {
                "total_customers": customer_analysis.get("total_customers", 0),
                "top_customers": customer_analysis.get("top_customers", [])[:3],
                "segments": customer_analysis.get("segments", {}),
                "avg_customer_value": customer_analysis.get("avg_customer_value", 0)
            },
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_detailed_sales_report(
        self, 
        start_date: date, 
        end_date: date,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """Gerar relatório detalhado de vendas"""
        
        # Performance por período
        performance = self.analytics.get_sales_performance(start_date, end_date, group_by)
        
        # Análise de receita
        revenue_analysis = self.analytics.get_revenue_analysis(start_date, end_date, group_by)
        
        # Análise de sazonalidade
        seasonality = self.analytics.get_seasonality_analysis(start_date, end_date)
        
        # Produtos por categoria
        categories_performance = {}
        for category_data in self.analytics.get_market_share(start_date, end_date, "category"):
            category = category_data["segment"]
            categories_performance[category] = {
                "revenue": category_data["revenue"],
                "market_share": category_data["market_share_pct"],
                "top_products": self.analytics.get_top_products(
                    start_date, end_date, "revenue", 5
                )
            }
        
        # Análise geográfica (por localização)
        geographic_analysis = self.analytics.get_market_share(start_date, end_date, "location")
        
        return {
            "period": f"{start_date} to {end_date}",
            "grouping": group_by,
            "performance": performance,
            "revenue_analysis": revenue_analysis,
            "seasonality": seasonality,
            "categories": categories_performance,
            "geographic": geographic_analysis[:10],  # Top 10 localizações
            "summary_stats": self._calculate_detailed_stats(performance),
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_product_performance_report(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Relatório específico de performance de produtos"""
        
        # Top produtos por diferentes métricas
        top_by_revenue = self.analytics.get_top_products(start_date, end_date, "revenue", 20)
        top_by_quantity = self.analytics.get_top_products(start_date, end_date, "quantity", 20)
        top_by_frequency = self.analytics.get_top_products(start_date, end_date, "frequency", 20)
        
        # Análise por categoria
        category_performance = {}
        categories = self.analytics.get_market_share(start_date, end_date, "category")
        
        for cat in categories:
            category_name = cat["segment"]
            category_performance[category_name] = {
                "total_revenue": cat["revenue"],
                "market_share": cat["market_share_pct"],
                "product_count": len([p for p in top_by_revenue if p["product_category"] == category_name]),
                "avg_product_revenue": cat["revenue"] / max(1, len([p for p in top_by_revenue if p["product_category"] == category_name]))
            }
        
        # Produtos com baixa performance (possíveis descontinuações)
        low_performers = self._identify_low_performers(start_date, end_date)
        
        # Produtos em crescimento
        growth_products = self._identify_growth_products(start_date, end_date)
        
        return {
            "period": f"{start_date} to {end_date}",
            "top_performers": {
                "by_revenue": top_by_revenue[:10],
                "by_quantity": top_by_quantity[:10],
                "by_frequency": top_by_frequency[:10]
            },
            "category_analysis": category_performance,
            "low_performers": low_performers,
            "growth_opportunities": growth_products,
            "product_insights": self._generate_product_insights(top_by_revenue, categories),
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_customer_analysis_report(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Relatório de análise de clientes/farmácias"""
        
        customer_analysis = self.analytics.get_customer_analysis(start_date, end_date)
        
        # Análise RFM (Recency, Frequency, Monetary)
        rfm_analysis = self._perform_rfm_analysis(start_date, end_date)
        
        # Análise de retenção
        retention_analysis = self._analyze_customer_retention(start_date, end_date)
        
        # Segmentação avançada
        customer_segments = self._advanced_customer_segmentation(customer_analysis)
        
        # Oportunidades de cross-sell
        cross_sell_opportunities = self._identify_cross_sell_opportunities(start_date, end_date)
        
        return {
            "period": f"{start_date} to {end_date}",
            "overview": customer_analysis,
            "rfm_analysis": rfm_analysis,
            "retention": retention_analysis,
            "segmentation": customer_segments,
            "cross_sell_opportunities": cross_sell_opportunities,
            "customer_insights": self._generate_customer_insights(customer_analysis),
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_pdf_report(
        self, 
        report_data: Dict[str, Any], 
        report_type: str = "executive"
    ) -> io.BytesIO:
        """Gerar relatório em PDF"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.darkblue
        )
        
        story.append(Paragraph("QSDPharmalitics - Relatório Executivo", title_style))
        story.append(Spacer(1, 20))
        
        # Informações do período
        period_text = f"<b>Período:</b> {report_data.get('period', {}).get('current', 'N/A')}"
        story.append(Paragraph(period_text, styles['Normal']))
        
        generation_date = f"<b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        story.append(Paragraph(generation_date, styles['Normal']))
        story.append(Spacer(1, 30))
        
        # KPIs Principais
        if 'kpis' in report_data:
            story.append(Paragraph("📊 Indicadores Principais", styles['Heading2']))
            
            kpis_data = []
            for kpi_name, kpi_value in report_data['kpis'].items():
                kpis_data.append([kpi_name.replace('_', ' ').title(), f"{kpi_value:,.2f}"])
            
            kpis_table = Table(kpis_data, colWidths=[3*inch, 2*inch])
            kpis_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(kpis_table)
            story.append(Spacer(1, 20))
        
        # Resumo Executivo
        if 'summary' in report_data:
            story.append(Paragraph("📈 Resumo do Período", styles['Heading2']))
            
            summary = report_data['summary']
            summary_text = f"""
            <b>Receita Total:</b> R$ {summary.get('total_revenue', 0):,.2f}<br/>
            <b>Total de Transações:</b> {summary.get('total_transactions', 0):,}<br/>
            <b>Ticket Médio:</b> R$ {summary.get('avg_order_value', 0):,.2f}<br/>
            <b>Produtos Únicos:</b> {summary.get('unique_products', 0):,}<br/>
            <b>Farmácias Atendidas:</b> {summary.get('unique_pharmacies', 0):,}
            """
            
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Top Produtos
        if 'top_products' in report_data:
            story.append(Paragraph("🏆 Top 5 Produtos", styles['Heading2']))
            
            products_data = [['#', 'Produto', 'Categoria', 'Receita']]
            for i, product in enumerate(report_data['top_products'], 1):
                products_data.append([
                    str(i),
                    product['product_name'][:30],
                    product['product_category'],
                    f"R$ {product['revenue']:,.2f}"
                ])
            
            products_table = Table(products_data, colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 1.5*inch])
            products_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(products_table)
            story.append(Spacer(1, 20))
        
        # Insights
        if 'insights' in report_data:
            story.append(Paragraph("💡 Insights e Recomendações", styles['Heading2']))
            
            for insight in report_data['insights'][:5]:  # Máximo 5 insights
                insight_text = f"• {insight}"
                story.append(Paragraph(insight_text, styles['Normal']))
                story.append(Spacer(1, 10))
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def export_to_excel(
        self, 
        report_data: Dict[str, Any], 
        filename: Optional[str] = None
    ) -> io.BytesIO:
        """Exportar relatório para Excel com múltiplas abas"""
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Aba 1: Resumo
            if 'summary' in report_data:
                summary_df = pd.DataFrame([report_data['summary']])
                summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            # Aba 2: KPIs
            if 'kpis' in report_data:
                kpis_df = pd.DataFrame(list(report_data['kpis'].items()), 
                                     columns=['Indicador', 'Valor'])
                kpis_df.to_excel(writer, sheet_name='KPIs', index=False)
            
            # Aba 3: Top Produtos
            if 'top_products' in report_data:
                products_df = pd.DataFrame(report_data['top_products'])
                products_df.to_excel(writer, sheet_name='Top Produtos', index=False)
            
            # Aba 4: Performance
            if 'performance' in report_data:
                performance_df = pd.DataFrame(report_data['performance'])
                performance_df.to_excel(writer, sheet_name='Performance', index=False)
            
            # Aba 5: Market Share
            if 'market_share' in report_data:
                market_df = pd.DataFrame(report_data['market_share'])
                market_df.to_excel(writer, sheet_name='Market Share', index=False)
            
            # Aba 6: Clientes
            if 'customer_insights' in report_data and 'top_customers' in report_data['customer_insights']:
                customers_df = pd.DataFrame(report_data['customer_insights']['top_customers'])
                customers_df.to_excel(writer, sheet_name='Top Clientes', index=False)
        
        output.seek(0)
        return output
    
    # Métodos auxiliares privados
    
    def _calculate_key_kpis(
        self, 
        current_summary: Dict[str, Any], 
        comparisons: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcular KPIs principais"""
        
        return {
            "receita_total": current_summary.get("total_revenue", 0),
            "crescimento_receita": comparisons.get("revenue", {}).get("change_pct", 0),
            "ticket_medio": current_summary.get("avg_order_value", 0),
            "total_transacoes": current_summary.get("total_transactions", 0),
            "produtos_unicos": current_summary.get("unique_products", 0),
            "farmácias_ativas": current_summary.get("unique_pharmacies", 0)
        }
    
    def _generate_insights(
        self, 
        current: Dict[str, Any], 
        previous: Dict[str, Any],
        top_products: List[Dict[str, Any]],
        market_share: List[Dict[str, Any]]
    ) -> List[str]:
        """Gerar insights automáticos"""
        
        insights = []
        
        # Insight sobre crescimento de receita
        revenue_growth = ((current.get("total_revenue", 0) - previous.get("total_revenue", 0)) / 
                         max(previous.get("total_revenue", 1), 1)) * 100
        
        if revenue_growth > 10:
            insights.append(f"Excelente crescimento de receita: {revenue_growth:.1f}% vs período anterior")
        elif revenue_growth > 0:
            insights.append(f"Crescimento positivo de receita: {revenue_growth:.1f}% vs período anterior")
        else:
            insights.append(f"Receita em declínio: {revenue_growth:.1f}% vs período anterior - investigar causas")
        
        # Insight sobre concentração de produtos
        if top_products:
            top_5_revenue = sum([p["revenue"] for p in top_products[:5]])
            total_revenue = current.get("total_revenue", 1)
            concentration = (top_5_revenue / total_revenue) * 100
            
            if concentration > 80:
                insights.append(f"Alta concentração: Top 5 produtos representam {concentration:.1f}% da receita")
            elif concentration < 50:
                insights.append(f"Receita bem distribuída: Top 5 produtos representam {concentration:.1f}% da receita")
        
        # Insight sobre ticket médio
        avg_order_current = current.get("avg_order_value", 0)
        avg_order_previous = previous.get("avg_order_value", 0)
        
        if avg_order_current > avg_order_previous * 1.05:
            insights.append("Ticket médio em crescimento - estratégia de preços funcionando")
        elif avg_order_current < avg_order_previous * 0.95:
            insights.append("Ticket médio em declínio - avaliar estratégia de preços")
        
        # Insight sobre diversificação
        unique_products = current.get("unique_products", 0)
        if unique_products > 50:
            insights.append("Portfolio diversificado com mais de 50 produtos únicos")
        elif unique_products < 20:
            insights.append("Portfolio concentrado - considerar expansão de produtos")
        
        return insights
    
    def _calculate_detailed_stats(self, performance: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcular estatísticas detalhadas"""
        
        if not performance:
            return {}
        
        revenues = [p.get("revenue", 0) for p in performance]
        quantities = [p.get("quantity", 0) for p in performance]
        
        return {
            "receita_media_periodo": sum(revenues) / len(revenues),
            "receita_maxima": max(revenues),
            "receita_minima": min(revenues),
            "quantidade_media_periodo": sum(quantities) / len(quantities),
            "total_periodos": len(performance),
            "periodos_com_vendas": len([r for r in revenues if r > 0])
        }
    
    def _identify_low_performers(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Identificar produtos com baixa performance"""
        
        all_products = self.analytics.get_top_products(start_date, end_date, "revenue", 1000)
        
        # Produtos no último quartil de performance
        if len(all_products) > 4:
            cutoff = len(all_products) * 0.75
            low_performers = all_products[int(cutoff):]
            
            return [{
                "product_name": p["product_name"],
                "product_category": p["product_category"],
                "revenue": p["revenue"],
                "reason": "Baixa receita em comparação com outros produtos"
            } for p in low_performers[:10]]
        
        return []
    
    def _identify_growth_products(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Identificar produtos em crescimento"""
        
        # Comparar primeira vs segunda metade do período
        mid_point = start_date + (end_date - start_date) / 2
        
        first_half = self.analytics.get_top_products(start_date, mid_point, "revenue", 50)
        second_half = self.analytics.get_top_products(mid_point, end_date, "revenue", 50)
        
        growth_products = []
        
        for product_second in second_half:
            # Procurar mesmo produto na primeira metade
            first_half_product = next(
                (p for p in first_half if p["product_name"] == product_second["product_name"]), 
                None
            )
            
            if first_half_product:
                growth_rate = ((product_second["revenue"] - first_half_product["revenue"]) /
                             max(first_half_product["revenue"], 1)) * 100
                
                if growth_rate > 20:  # Crescimento > 20%
                    growth_products.append({
                        "product_name": product_second["product_name"],
                        "product_category": product_second["product_category"],
                        "growth_rate": growth_rate,
                        "first_half_revenue": first_half_product["revenue"],
                        "second_half_revenue": product_second["revenue"]
                    })
        
        return sorted(growth_products, key=lambda x: x["growth_rate"], reverse=True)[:10]
    
    def _generate_product_insights(
        self, 
        top_products: List[Dict[str, Any]], 
        categories: List[Dict[str, Any]]
    ) -> List[str]:
        """Gerar insights sobre produtos"""
        
        insights = []
        
        if top_products:
            # Produto líder
            leader = top_products[0]
            insights.append(f"Produto líder: {leader['product_name']} com R$ {leader['revenue']:,.2f}")
            
            # Categoria dominante
            category_revenues = {}
            for product in top_products[:10]:
                cat = product["product_category"]
                category_revenues[cat] = category_revenues.get(cat, 0) + product["revenue"]
            
            dominant_category = max(category_revenues.items(), key=lambda x: x[1])
            insights.append(f"Categoria dominante no top 10: {dominant_category[0]}")
        
        return insights
    
    def _perform_rfm_analysis(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Análise RFM simplificada"""
        
        customer_analysis = self.analytics.get_customer_analysis(start_date, end_date)
        customers = customer_analysis.get("top_customers", [])
        
        if not customers:
            return {"error": "Dados insuficientes para análise RFM"}
        
        # Calcular quartis para segmentação
        revenues = [c["total_revenue"] for c in customers]
        frequencies = [c["total_orders"] for c in customers]
        
        revenue_quartiles = pd.Series(revenues).quantile([0.25, 0.5, 0.75]).tolist()
        frequency_quartiles = pd.Series(frequencies).quantile([0.25, 0.5, 0.75]).tolist()
        
        segments = {"Champions": 0, "Potential": 0, "At Risk": 0, "Lost": 0}
        
        for customer in customers:
            revenue = customer["total_revenue"]
            frequency = customer["total_orders"]
            
            # Segmentação simplificada
            if revenue >= revenue_quartiles[2] and frequency >= frequency_quartiles[2]:
                segments["Champions"] += 1
            elif revenue >= revenue_quartiles[1] or frequency >= frequency_quartiles[1]:
                segments["Potential"] += 1
            elif revenue >= revenue_quartiles[0]:
                segments["At Risk"] += 1
            else:
                segments["Lost"] += 1
        
        return {
            "segments": segments,
            "total_analyzed": len(customers),
            "quartiles": {
                "revenue": revenue_quartiles,
                "frequency": frequency_quartiles
            }
        }
    
    def _analyze_customer_retention(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Análise de retenção de clientes"""
        
        # Análise simplificada baseada em frequência de compras
        period_length = (end_date - start_date).days
        
        if period_length < 60:
            return {"error": "Período muito curto para análise de retenção"}
        
        mid_point = start_date + timedelta(days=period_length // 2)
        
        first_half_customers = set()
        second_half_customers = set()
        
        # Query para primeira metade
        first_half_sales = self.db.query(Sale.pharmacy_name).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date < mid_point,
            Sale.is_active == True,
            Sale.pharmacy_name.isnot(None)
        ).distinct().all()
        
        first_half_customers = {sale.pharmacy_name for sale in first_half_sales}
        
        # Query para segunda metade
        second_half_sales = self.db.query(Sale.pharmacy_name).filter(
            Sale.sale_date >= mid_point,
            Sale.sale_date <= end_date,
            Sale.is_active == True,
            Sale.pharmacy_name.isnot(None)
        ).distinct().all()
        
        second_half_customers = {sale.pharmacy_name for sale in second_half_sales}
        
        # Calcular métricas
        retained = first_half_customers.intersection(second_half_customers)
        new_customers = second_half_customers - first_half_customers
        churned = first_half_customers - second_half_customers
        
        retention_rate = (len(retained) / max(len(first_half_customers), 1)) * 100
        
        return {
            "retention_rate": retention_rate,
            "retained_customers": len(retained),
            "new_customers": len(new_customers),
            "churned_customers": len(churned),
            "total_first_half": len(first_half_customers),
            "total_second_half": len(second_half_customers)
        }
    
    def _advanced_customer_segmentation(
        self, 
        customer_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Segmentação avançada de clientes"""
        
        customers = customer_analysis.get("top_customers", [])
        
        if not customers:
            return {"error": "Dados insuficientes para segmentação"}
        
        # Segmentação por valor e frequência
        segments = {
            "VIP": [],          # Alto valor, alta frequência
            "Crescimento": [],  # Médio valor, alta frequência
            "Potencial": [],    # Alto valor, baixa frequência
            "Básico": []        # Baixo valor, baixa frequência
        }
        
        revenues = [c["total_revenue"] for c in customers]
        frequencies = [c["total_orders"] for c in customers]
        
        avg_revenue = sum(revenues) / len(revenues)
        avg_frequency = sum(frequencies) / len(frequencies)
        
        for customer in customers:
            revenue = customer["total_revenue"]
            frequency = customer["total_orders"]
            
            if revenue >= avg_revenue and frequency >= avg_frequency:
                segments["VIP"].append(customer)
            elif revenue < avg_revenue and frequency >= avg_frequency:
                segments["Crescimento"].append(customer)
            elif revenue >= avg_revenue and frequency < avg_frequency:
                segments["Potencial"].append(customer)
            else:
                segments["Básico"].append(customer)
        
        return {
            "segments": {k: len(v) for k, v in segments.items()},
            "segment_details": segments,
            "criteria": {
                "avg_revenue": avg_revenue,
                "avg_frequency": avg_frequency
            }
        }
    
    def _identify_cross_sell_opportunities(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Identificar oportunidades de cross-sell"""
        
        # Análise simplificada de produtos frequentemente comprados juntos
        # Agrupar por farmácia e identificar padrões
        
        opportunities = []
        
        # Por enquanto, retornar análise básica de categorias por cliente
        top_customers = self.analytics.get_customer_analysis(start_date, end_date)
        customers = top_customers.get("top_customers", [])[:10]
        
        for customer in customers:
            # Buscar categorias compradas por este cliente
            customer_sales = self.db.query(Sale.product_category).filter(
                Sale.pharmacy_name == customer["pharmacy_name"],
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.is_active == True
            ).distinct().all()
            
            categories = [sale.product_category for sale in customer_sales]
            
            # Sugerir categorias não compradas
            all_categories = ["Analgésicos", "Anti-inflamatórios", "Antibióticos", 
                            "Anti-hipertensivos", "Antidiabéticos", "Gastroprotetores"]
            
            missing_categories = [cat for cat in all_categories if cat not in categories]
            
            if missing_categories:
                opportunities.append({
                    "customer": customer["pharmacy_name"],
                    "current_categories": categories,
                    "opportunities": missing_categories[:3],  # Top 3 sugestões
                    "potential_value": customer["avg_order_value"] * len(missing_categories)
                })
        
        return opportunities[:5]  # Top 5 oportunidades
    
    def _generate_customer_insights(
        self, 
        customer_analysis: Dict[str, Any]
    ) -> List[str]:
        """Gerar insights sobre clientes"""
        
        insights = []
        
        total_customers = customer_analysis.get("total_customers", 0)
        avg_customer_value = customer_analysis.get("avg_customer_value", 0)
        top_customers = customer_analysis.get("top_customers", [])
        
        if total_customers > 0:
            insights.append(f"Base ativa de {total_customers} farmácias clientes")
        
        if avg_customer_value > 0:
            insights.append(f"Valor médio por cliente: R$ {avg_customer_value:,.2f}")
        
        if top_customers:
            top_customer = top_customers[0]
            insights.append(f"Maior cliente: {top_customer['pharmacy_name']} - R$ {top_customer['total_revenue']:,.2f}")
            
            # Análise de concentração
            top_5_revenue = sum([c["total_revenue"] for c in top_customers[:5]])
            total_revenue = sum([c["total_revenue"] for c in top_customers])
            
            if total_revenue > 0:
                concentration = (top_5_revenue / total_revenue) * 100
                insights.append(f"Top 5 clientes representam {concentration:.1f}% da receita")
        
        return insights