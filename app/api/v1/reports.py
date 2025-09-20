from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime, timedelta
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from app.database import get_db
from app.core.analytics import AnalyticsService
from app.models.sales import Sale

router = APIRouter()

# ========== REPORTS ENDPOINTS ==========

@router.get("/sales-summary")
async def sales_summary_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = Query("json", regex="^(json|csv|excel)$"),
    db: Session = Depends(get_db)
):
    """
    Relatório resumo de vendas
    Formatos: json, csv, excel
    """
    analytics = AnalyticsService(db)
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Dados do relatório
    summary = analytics.get_performance_summary(start_date, end_date)
    top_products = analytics.get_top_products(start_date, end_date, "revenue", 10)
    market_share = analytics.get_market_share(start_date, end_date, "category")
    
    report_data = {
        "period": f"{start_date} to {end_date}",
        "summary": summary,
        "top_products": top_products,
        "market_share": market_share,
        "generated_at": datetime.now().isoformat()
    }
    
    if format == "json":
        return report_data
    elif format == "csv":
        return await export_summary_csv(report_data)
    elif format == "excel":
        return await export_summary_excel(report_data)

@router.get("/monthly")
async def monthly_report(
    year: int = Query(datetime.now().year),
    month: int = Query(datetime.now().month, ge=1, le=12),
    db: Session = Depends(get_db)
):
    """Relatório mensal detalhado"""
    analytics = AnalyticsService(db)
    
    # Definir período do mês
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Dados do relatório mensal
    monthly_data = {
        "period": f"{start_date.strftime('%B %Y')}",
        "start_date": start_date,
        "end_date": end_date,
        "summary": analytics.get_performance_summary(start_date, end_date),
        "daily_performance": analytics.get_sales_performance(start_date, end_date, "day"),
        "top_products": analytics.get_top_products(start_date, end_date, "revenue", 15),
        "customer_analysis": analytics.get_customer_analysis(start_date, end_date),
        "revenue_breakdown": analytics.get_revenue_analysis(start_date, end_date, "week"),
        "market_share": analytics.get_market_share(start_date, end_date, "category"),
        "growth_analysis": analytics.calculate_growth_rate(start_date, end_date),
        "generated_at": datetime.now().isoformat()
    }
    
    return monthly_data

@router.get("/comparative")
async def comparative_report(
    start_date_1: date,
    end_date_1: date,
    start_date_2: date,
    end_date_2: date,
    db: Session = Depends(get_db)
):
    """Relatório comparativo entre dois períodos"""
    analytics = AnalyticsService(db)
    
    period_1_data = {
        "period": f"{start_date_1} to {end_date_1}",
        "summary": analytics.get_performance_summary(start_date_1, end_date_1),
        "top_products": analytics.get_top_products(start_date_1, end_date_1, "revenue", 10),
        "market_share": analytics.get_market_share(start_date_1, end_date_1, "category")
    }
    
    period_2_data = {
        "period": f"{start_date_2} to {end_date_2}",
        "summary": analytics.get_performance_summary(start_date_2, end_date_2),
        "top_products": analytics.get_top_products(start_date_2, end_date_2, "revenue", 10),
        "market_share": analytics.get_market_share(start_date_2, end_date_2, "category")
    }
    
    # Comparação entre períodos
    comparison = analytics.compare_periods(
        period_1_data["summary"], 
        period_2_data["summary"]
    )
    
    return {
        "period_1": period_1_data,
        "period_2": period_2_data,
        "comparison": comparison,
        "generated_at": datetime.now().isoformat()
    }

@router.get("/export/csv")
async def export_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    report_type: str = Query("sales", regex="^(sales|products|customers)$"),
    db: Session = Depends(get_db)
):
    """Exportar dados em CSV"""
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    if report_type == "sales":
        return await export_sales_csv(start_date, end_date, db)
    elif report_type == "products":
        return await export_products_csv(start_date, end_date, db)
    elif report_type == "customers":
        return await export_customers_csv(start_date, end_date, db)

@router.get("/export/excel")
async def export_excel(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Exportar relatório completo em Excel"""
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    return await export_full_excel_report(start_date, end_date, db)

@router.get("/export/pdf")
async def export_pdf(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Exportar relatório em PDF"""
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    return await generate_pdf_report(start_date, end_date, db)

# ========== HELPER FUNCTIONS ==========

async def export_sales_csv(start_date: date, end_date: date, db: Session):
    """Exportar vendas em CSV"""
    
    # Query das vendas
    sales_query = db.query(Sale).filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date,
        Sale.is_active == True
    ).order_by(Sale.sale_date.desc())
    
    # Converter para DataFrame
    sales_data = []
    for sale in sales_query.all():
        sales_data.append({
            'ID': sale.id,
            'Data': sale.sale_date.strftime('%Y-%m-%d'),
            'Produto': sale.product_name,
            'Categoria': sale.product_category,
            'Código': sale.product_code,
            'Quantidade': sale.quantity,
            'Preço Unitário': sale.unit_price,
            'Desconto': sale.discount or 0,
            'Total': sale.total_price,
            'Farmácia': sale.pharmacy_name or '',
            'Localização': sale.pharmacy_location or '',
            'Tipo Cliente': sale.customer_type or '',
            'Forma Pagamento': sale.payment_method or '',
            'Representante': sale.sales_rep or '',
            'Campanha': sale.campaign_id or '',
            'Observações': sale.notes or ''
        })
    
    df = pd.DataFrame(sales_data)
    
    # Criar CSV em memória
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    
    # Retornar como streaming response
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=vendas_{start_date}_a_{end_date}.csv"}
    )

async def export_products_csv(start_date: date, end_date: date, db: Session):
    """Exportar performance de produtos em CSV"""
    
    analytics = AnalyticsService(db)
    products_data = analytics.get_top_products(start_date, end_date, "revenue", 1000)
    
    df = pd.DataFrame(products_data)
    df.columns = ['Produto', 'Categoria', 'Receita', 'Quantidade', 'Frequência', 'Ticket Médio']
    
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=produtos_{start_date}_a_{end_date}.csv"}
    )

async def export_customers_csv(start_date: date, end_date: date, db: Session):
    """Exportar análise de clientes em CSV"""
    
    analytics = AnalyticsService(db)
    customer_data = analytics.get_customer_analysis(start_date, end_date)
    
    df = pd.DataFrame(customer_data.get("top_customers", []))
    if not df.empty:
        df.columns = ['Farmácia', 'Receita Total', 'Quantidade Total', 'Pedidos', 'Ticket Médio', 'Último Pedido']
    
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=clientes_{start_date}_a_{end_date}.csv"}
    )

async def export_full_excel_report(start_date: date, end_date: date, db: Session):
    """Exportar relatório completo em Excel com múltiplas abas"""
    
    analytics = AnalyticsService(db)
    
    # Criar arquivo Excel em memória
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Aba 1: Resumo
        summary_data = analytics.get_performance_summary(start_date, end_date)
        summary_df = pd.DataFrame([summary_data])
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
        
        # Aba 2: Vendas Diárias
        daily_performance = analytics.get_sales_performance(start_date, end_date, "day")
        daily_df = pd.DataFrame(daily_performance)
        daily_df.to_excel(writer, sheet_name='Performance Diária', index=False)
        
        # Aba 3: Top Produtos
        top_products = analytics.get_top_products(start_date, end_date, "revenue", 50)
        products_df = pd.DataFrame(top_products)
        products_df.to_excel(writer, sheet_name='Top Produtos', index=False)
        
        # Aba 4: Market Share
        market_share = analytics.get_market_share(start_date, end_date, "category")
        market_df = pd.DataFrame(market_share)
        market_df.to_excel(writer, sheet_name='Market Share', index=False)
        
        # Aba 5: Análise de Clientes
        customer_analysis = analytics.get_customer_analysis(start_date, end_date)
        customers_df = pd.DataFrame(customer_analysis.get("top_customers", []))
        customers_df.to_excel(writer, sheet_name='Análise Clientes', index=False)
        
        # Aba 6: Dados Brutos de Vendas
        sales_query = db.query(Sale).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.is_active == True
        ).limit(5000)  # Limitar para não sobrecarregar
        
        sales_data = []
        for sale in sales_query.all():
            sales_data.append({
                'Data': sale.sale_date.strftime('%Y-%m-%d'),
                'Produto': sale.product_name,
                'Categoria': sale.product_category,
                'Quantidade': sale.quantity,
                'Preço Unitário': sale.unit_price,
                'Total': sale.total_price,
                'Farmácia': sale.pharmacy_name or '',
                'Localização': sale.pharmacy_location or ''
            })
        
        sales_df = pd.DataFrame(sales_data)
        sales_df.to_excel(writer, sheet_name='Dados Vendas', index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=relatorio_completo_{start_date}_a_{end_date}.xlsx"}
    )

async def generate_pdf_report(start_date: date, end_date: date, db: Session):
    """Gerar relatório em PDF"""
    
    analytics = AnalyticsService(db)
    buffer = io.BytesIO()
    
    # Criar PDF
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Título
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "QSDPharmalitics - Relatório de Vendas")
    
    # Período
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Período: {start_date} a {end_date}")
    p.drawString(50, height - 100, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Resumo
    summary = analytics.get_performance_summary(start_date, end_date)
    
    y_position = height - 140
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Resumo Executivo")
    
    y_position -= 30
    p.setFont("Helvetica", 11)
    p.drawString(70, y_position, f"Receita Total: R$ {summary['total_revenue']:,.2f}")
    
    y_position -= 20
    p.drawString(70, y_position, f"Total de Transações: {summary['total_transactions']:,}")
    
    y_position -= 20
    p.drawString(70, y_position, f"Ticket Médio: R$ {summary['avg_order_value']:,.2f}")
    
    y_position -= 20
    p.drawString(70, y_position, f"Produtos Únicos: {summary['unique_products']:,}")
    
    y_position -= 20
    p.drawString(70, y_position, f"Farmácias Atendidas: {summary['unique_pharmacies']:,}")
    
    # Top 5 Produtos
    y_position -= 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Top 5 Produtos por Receita")
    
    top_products = analytics.get_top_products(start_date, end_date, "revenue", 5)
    
    y_position -= 30
    p.setFont("Helvetica", 10)
    for i, product in enumerate(top_products, 1):
        p.drawString(70, y_position, f"{i}. {product['product_name']}")
        p.drawString(300, y_position, f"R$ {product['revenue']:,.2f}")
        y_position -= 15
    
    # Market Share por Categoria
    y_position -= 30
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Market Share por Categoria")
    
    market_share = analytics.get_market_share(start_date, end_date, "category")[:5]
    
    y_position -= 30
    p.setFont("Helvetica", 10)
    for category in market_share:
        p.drawString(70, y_position, f"{category['segment']}")
        p.drawString(300, y_position, f"{category['market_share_pct']:.1f}%")
        p.drawString(400, y_position, f"R$ {category['revenue']:,.2f}")
        y_position -= 15
    
    # Finalizar PDF
    p.showPage()
    p.save()
    
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_{start_date}_a_{end_date}.pdf"}
    )

async def export_summary_csv(report_data):
    """Exportar resumo em CSV"""
    
    # Criar DataFrames dos diferentes dados
    summary_df = pd.DataFrame([report_data['summary']])
    products_df = pd.DataFrame(report_data['top_products'])
    market_df = pd.DataFrame(report_data['market_share'])
    
    output = io.StringIO()
    
    # Escrever múltiplas seções no CSV
    output.write("=== RESUMO GERAL ===\n")
    summary_df.to_csv(output, index=False)
    
    output.write("\n=== TOP PRODUTOS ===\n")
    products_df.to_csv(output, index=False)
    
    output.write("\n=== MARKET SHARE ===\n")
    market_df.to_csv(output, index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=resumo_vendas.csv"}
    )

async def export_summary_excel(report_data):
    """Exportar resumo em Excel"""
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Resumo
        summary_df = pd.DataFrame([report_data['summary']])
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
        
        # Top Produtos
        products_df = pd.DataFrame(report_data['top_products'])
        products_df.to_excel(writer, sheet_name='Top Produtos', index=False)
        
        # Market Share
        market_df = pd.DataFrame(report_data['market_share'])
        market_df.to_excel(writer, sheet_name='Market Share', index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=resumo_vendas.xlsx"}
    )