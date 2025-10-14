from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import os
import pandas as pd
from io import StringIO, BytesIO

from backend.database.base import get_db
from backend.api.dependencies import get_current_active_user, get_analyst_or_admin_user
from backend.schemas.reports import ReportRequest, ReportResponse, ReportListResponse, ReportType, ReportFormat
from backend.models.analytics import ReportGeneration
from backend.models.sales import Sale
from backend.models.products import Product
from backend.models.pharmacies import Pharmacy
from backend.models.user import User
from backend.core.config import settings

router = APIRouter()


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a new report"""
    
    # Create report generation record
    db_report = ReportGeneration(
        report_name=report_request.report_name,
        report_type=report_request.report_type,
        format_type=report_request.format_type.value,
        generated_by_user_id=current_user.id,
        date_range_start=report_request.date_range_start,
        date_range_end=report_request.date_range_end,
        filters_applied=report_request.filters,
        status="pending"
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # Add background task to generate the actual report
    background_tasks.add_task(
        _generate_report_file, 
        db_report.id, 
        report_request, 
        current_user.id
    )
    
    return _convert_to_response(db_report, current_user.full_name)


@router.get("/", response_model=ReportListResponse)
async def get_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    report_type: Optional[ReportType] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of generated reports"""
    
    query = db.query(ReportGeneration)
    
    # Non-admin users can only see their own reports
    if not current_user.is_admin:
        query = query.filter(ReportGeneration.generated_by_user_id == current_user.id)
    
    # Apply filters
    if report_type:
        query = query.filter(ReportGeneration.report_type == report_type)
    if status:
        query = query.filter(ReportGeneration.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    reports = query.order_by(ReportGeneration.generation_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Convert to response format
    items = [_convert_to_response(report, "System") for report in reports]
    
    return ReportListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific report"""
    
    query = db.query(ReportGeneration).filter(ReportGeneration.id == report_id)
    
    # Non-admin users can only access their own reports
    if not current_user.is_admin:
        query = query.filter(ReportGeneration.generated_by_user_id == current_user.id)
    
    report = query.first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return _convert_to_response(report, "System")


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download a generated report file"""
    
    query = db.query(ReportGeneration).filter(ReportGeneration.id == report_id)
    
    # Non-admin users can only download their own reports
    if not current_user.is_admin:
        query = query.filter(ReportGeneration.generated_by_user_id == current_user.id)
    
    report = query.first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.status != "completed" or not report.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is not ready for download"
        )
    
    # Check if file exists
    if not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    # Update download count
    report.download_count += 1
    db.commit()
    
    # Return file (in a real implementation, you'd use FileResponse)
    from fastapi.responses import FileResponse
    return FileResponse(
        path=report.file_path,
        filename=f"{report.report_name}.{report.format_type}",
        media_type="application/octet-stream"
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a report"""
    
    query = db.query(ReportGeneration).filter(ReportGeneration.id == report_id)
    
    # Non-admin users can only delete their own reports
    if not current_user.is_admin:
        query = query.filter(ReportGeneration.generated_by_user_id == current_user.id)
    
    report = query.first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Delete file if exists
    if report.file_path and os.path.exists(report.file_path):
        os.remove(report.file_path)
    
    # Delete database record
    db.delete(report)
    db.commit()


async def _generate_report_file(report_id: int, report_request: ReportRequest, user_id: int):
    """Background task to generate report file"""
    from database.base import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Get report record
        report = db.query(ReportGeneration).filter(ReportGeneration.id == report_id).first()
        
        if not report:
            return
        
        start_time = datetime.utcnow()
        
        # Get data based on report type
        if report_request.report_type == ReportType.SALES_SUMMARY:
            data = _get_sales_summary_data(db, report_request)
        elif report_request.report_type == ReportType.MONTHLY_REPORT:
            data = _get_monthly_report_data(db, report_request)
        elif report_request.report_type == ReportType.PRODUCT_ANALYSIS:
            data = _get_product_analysis_data(db, report_request)
        else:
            data = _get_sales_summary_data(db, report_request)  # Default
        
        # Generate file
        file_path = _create_report_file(data, report_request, report_id)
        
        # Update report record
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        report.file_path = file_path
        report.file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        report.total_records = len(data) if isinstance(data, list) else 0
        report.generation_duration = duration
        report.status = "completed"
        
        db.commit()
        
    except Exception as e:
        # Mark as failed
        report.status = "failed"
        report.error_message = str(e)
        db.commit()
        
    finally:
        db.close()


def _get_sales_summary_data(db: Session, request: ReportRequest) -> List[dict]:
    """Get sales summary data"""
    
    query = db.query(Sale).filter(
        Sale.is_active == True,
        Sale.sale_date >= request.date_range_start,
        Sale.sale_date <= request.date_range_end
    )
    
    # Apply filters if provided
    if request.filters:
        if 'product_ids' in request.filters:
            query = query.filter(Sale.product_id.in_(request.filters['product_ids']))
        if 'pharmacy_ids' in request.filters:
            query = query.filter(Sale.pharmacy_id.in_(request.filters['pharmacy_ids']))
    
    sales = query.all()
    
    return [
        {
            'Sale ID': sale.id,
            'Order Number': sale.order_number,
            'Sale Date': sale.sale_date.strftime('%Y-%m-%d'),
            'Product': sale.product.name if sale.product else 'Unknown',
            'Pharmacy': sale.pharmacy.name if sale.pharmacy else 'Unknown',
            'Quantity': sale.quantity,
            'Unit Price': float(sale.unit_price),
            'Total Amount': float(sale.final_amount),
            'Status': sale.status.value,
            'Payment Method': sale.payment_method.value
        }
        for sale in sales
    ]


def _get_monthly_report_data(db: Session, request: ReportRequest) -> List[dict]:
    """Get monthly report data"""
    # Similar to sales summary but with monthly aggregation
    return _get_sales_summary_data(db, request)


def _get_product_analysis_data(db: Session, request: ReportRequest) -> List[dict]:
    """Get product analysis data"""
    from sqlalchemy import func
    
    query = db.query(
        Product.name,
        Product.code,
        func.sum(Sale.quantity).label('total_quantity'),
        func.sum(Sale.final_amount).label('total_revenue'),
        func.count(Sale.id).label('total_orders'),
        func.avg(Sale.unit_price).label('avg_price')
    ).join(Sale.product)\
     .filter(
         Sale.is_active == True,
         Sale.sale_date >= request.date_range_start,
         Sale.sale_date <= request.date_range_end
     )\
     .group_by(Product.id, Product.name, Product.code)
    
    results = query.all()
    
    return [
        {
            'Product Name': result.name,
            'Product Code': result.code,
            'Total Quantity Sold': int(result.total_quantity),
            'Total Revenue': float(result.total_revenue),
            'Total Orders': int(result.total_orders),
            'Average Price': float(result.avg_price)
        }
        for result in results
    ]


def _create_report_file(data: List[dict], request: ReportRequest, report_id: int) -> str:
    """Create report file in specified format"""
    
    # Ensure reports directory exists
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    
    # Create filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{request.report_type.value}_{report_id}_{timestamp}.{request.format_type.value}"
    file_path = os.path.join(settings.REPORTS_DIR, filename)
    
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    if request.format_type == ReportFormat.CSV:
        df.to_csv(file_path, index=False)
    elif request.format_type == ReportFormat.EXCEL:
        df.to_excel(file_path, index=False, engine='openpyxl')
    elif request.format_type == ReportFormat.PDF:
        # For PDF, we'd use reportlab or similar
        # For now, just create a simple CSV and rename it
        df.to_csv(file_path.replace('.pdf', '.csv'), index=False)
    
    return file_path


def _convert_to_response(report: ReportGeneration, generated_by: str) -> ReportResponse:
    """Convert ReportGeneration model to response"""
    
    return ReportResponse(
        id=report.id,
        report_name=report.report_name,
        report_type=ReportType(report.report_type),
        format_type=ReportFormat(report.format_type),
        status=report.status,
        file_path=report.file_path,
        file_size=report.file_size,
        download_count=report.download_count,
        generation_date=report.generation_date,
        generated_by=generated_by,
        date_range_start=report.date_range_start,
        date_range_end=report.date_range_end,
        total_records=report.total_records,
        generation_duration=report.generation_duration,
        expires_at=report.expires_at
    )