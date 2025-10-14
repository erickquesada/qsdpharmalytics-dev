from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from backend.database.base import get_db
from backend.api.dependencies import get_current_active_user, get_admin_user
from backend.schemas.sales import (
    SaleCreate, SaleUpdate, SaleResponse, SaleListResponse, 
    SalesSummary, SalesFilters
)
from backend.models.sales import Sale, SaleStatus, PaymentMethod
from backend.models.user import User
from backend.models.products import Product
from backend.models.pharmacies import Pharmacy

router = APIRouter()


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new sale"""
    
    # Verify product exists
    product = db.query(Product).filter(Product.id == sale.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Verify pharmacy exists
    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == sale.pharmacy_id).first()
    if not pharmacy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pharmacy not found"
        )
    
    # Create sale object
    db_sale = Sale(**sale.dict())
    
    # Set sales rep if not specified
    if not db_sale.sales_rep_id:
        db_sale.sales_rep_id = current_user.id
    
    # Calculate totals
    db_sale.calculate_totals()
    
    # Generate order number if not provided
    if not db_sale.order_number:
        db_sale.order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{db.query(Sale).count() + 1:06d}"
    
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    # Load related data
    db_sale = db.query(Sale)\
        .options(
            joinedload(Sale.product),
            joinedload(Sale.pharmacy),
            joinedload(Sale.sales_rep)
        )\
        .filter(Sale.id == db_sale.id)\
        .first()
    
    return _enrich_sale_response(db_sale)


@router.get("/", response_model=SaleListResponse)
async def get_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_id: Optional[int] = None,
    pharmacy_id: Optional[int] = None,
    sales_rep_id: Optional[int] = None,
    status: Optional[SaleStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sales with filtering and pagination"""
    
    # Build query
    query = db.query(Sale).options(
        joinedload(Sale.product),
        joinedload(Sale.pharmacy),
        joinedload(Sale.sales_rep)
    ).filter(Sale.is_active == True)
    
    # Apply role-based filtering
    if current_user.role.value == "sales_rep":
        query = query.filter(Sale.sales_rep_id == current_user.id)
    
    # Apply filters
    if product_id:
        query = query.filter(Sale.product_id == product_id)
    if pharmacy_id:
        query = query.filter(Sale.pharmacy_id == pharmacy_id)
    if sales_rep_id and current_user.is_admin:
        query = query.filter(Sale.sales_rep_id == sales_rep_id)
    if status:
        query = query.filter(Sale.status == status)
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    sales = query.order_by(desc(Sale.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Enrich responses
    enriched_sales = [_enrich_sale_response(sale) for sale in sales]
    
    return {
        "items": enriched_sales,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific sale by ID"""
    
    query = db.query(Sale)\
        .options(
            joinedload(Sale.product),
            joinedload(Sale.pharmacy),
            joinedload(Sale.sales_rep)
        )\
        .filter(Sale.id == sale_id, Sale.is_active == True)
    
    # Apply role-based filtering
    if current_user.role.value == "sales_rep":
        query = query.filter(Sale.sales_rep_id == current_user.id)
    
    sale = query.first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    return _enrich_sale_response(sale)


@router.put("/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: int,
    sale_update: SaleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a sale"""
    
    # Get existing sale
    query = db.query(Sale).filter(Sale.id == sale_id, Sale.is_active == True)
    
    # Apply role-based filtering
    if current_user.role.value == "sales_rep":
        query = query.filter(Sale.sales_rep_id == current_user.id)
    
    db_sale = query.first()
    
    if not db_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    # Update fields
    update_data = sale_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sale, field, value)
    
    # Recalculate totals if price or quantity changed
    if any(field in update_data for field in ['quantity', 'unit_price', 'discount_amount', 'tax_amount']):
        db_sale.calculate_totals()
    
    db.commit()
    db.refresh(db_sale)
    
    # Load related data
    db_sale = db.query(Sale)\
        .options(
            joinedload(Sale.product),
            joinedload(Sale.pharmacy),
            joinedload(Sale.sales_rep)
        )\
        .filter(Sale.id == db_sale.id)\
        .first()
    
    return _enrich_sale_response(db_sale)


@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Soft delete a sale (Admin only)"""
    
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.is_active == True).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    sale.is_active = False
    db.commit()


@router.get("/summary/overview", response_model=SalesSummary)
async def get_sales_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sales summary for a date range"""
    
    query = db.query(Sale).filter(Sale.is_active == True)
    
    # Apply role-based filtering
    if current_user.role.value == "sales_rep":
        query = query.filter(Sale.sales_rep_id == current_user.id)
    
    # Apply date filters
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    
    sales = query.all()
    
    if not sales:
        return SalesSummary(
            total_sales=0,
            total_revenue=Decimal(0),
            total_quantity=0,
            average_order_value=Decimal(0),
            period_start=start_date or datetime.now().date(),
            period_end=end_date or datetime.now().date()
        )
    
    total_sales = len(sales)
    total_revenue = sum(sale.final_amount for sale in sales)
    total_quantity = sum(sale.quantity for sale in sales)
    average_order_value = total_revenue / total_sales if total_sales > 0 else Decimal(0)
    
    # Get top product and pharmacy
    from sqlalchemy import func
    top_product_query = db.query(
        Product.name,
        func.sum(Sale.final_amount).label('revenue')
    ).join(Sale.product)\
     .filter(Sale.is_active == True)
    
    if start_date:
        top_product_query = top_product_query.filter(Sale.sale_date >= start_date)
    if end_date:
        top_product_query = top_product_query.filter(Sale.sale_date <= end_date)
    if current_user.role.value == "sales_rep":
        top_product_query = top_product_query.filter(Sale.sales_rep_id == current_user.id)
    
    top_product = top_product_query.group_by(Product.name)\
        .order_by(desc('revenue'))\
        .first()
    
    top_pharmacy_query = db.query(
        Pharmacy.name,
        func.sum(Sale.final_amount).label('revenue')
    ).join(Sale.pharmacy)\
     .filter(Sale.is_active == True)
    
    if start_date:
        top_pharmacy_query = top_pharmacy_query.filter(Sale.sale_date >= start_date)
    if end_date:
        top_pharmacy_query = top_pharmacy_query.filter(Sale.sale_date <= end_date)
    if current_user.role.value == "sales_rep":
        top_pharmacy_query = top_pharmacy_query.filter(Sale.sales_rep_id == current_user.id)
    
    top_pharmacy = top_pharmacy_query.group_by(Pharmacy.name)\
        .order_by(desc('revenue'))\
        .first()
    
    return SalesSummary(
        total_sales=total_sales,
        total_revenue=total_revenue,
        total_quantity=total_quantity,
        average_order_value=average_order_value,
        top_product=top_product.name if top_product else None,
        top_pharmacy=top_pharmacy.name if top_pharmacy else None,
        period_start=start_date or min(sale.sale_date for sale in sales).date(),
        period_end=end_date or max(sale.sale_date for sale in sales).date()
    )


def _enrich_sale_response(sale: Sale) -> dict:
    """Enrich sale response with additional data"""
    sale_dict = {
        "id": sale.id,
        "product_id": sale.product_id,
        "pharmacy_id": sale.pharmacy_id,
        "quantity": sale.quantity,
        "unit_price": sale.unit_price,
        "total_price": sale.total_price,
        "discount_amount": sale.discount_amount,
        "tax_amount": sale.tax_amount,
        "final_amount": sale.final_amount,
        "payment_method": sale.payment_method,
        "status": sale.status,
        "sale_date": sale.sale_date,
        "delivery_date": sale.delivery_date,
        "order_number": sale.order_number,
        "po_number": sale.po_number,
        "campaign_id": sale.campaign_id,
        "promotion_code": sale.promotion_code,
        "territory": sale.territory,
        "region": sale.region,
        "notes": sale.notes,
        "invoice_number": sale.invoice_number,
        "created_at": sale.created_at,
        "updated_at": sale.updated_at,
        
        # Related data
        "product_name": sale.product.name if sale.product else None,
        "product_code": sale.product.code if sale.product else None,
        "pharmacy_name": sale.pharmacy.name if sale.pharmacy else None,
        "pharmacy_location": sale.pharmacy.location if sale.pharmacy else None,
        "sales_rep_name": sale.sales_rep.full_name if sale.sales_rep else None,
        
        # Calculated fields
        "discount_percentage": sale.discount_percentage,
        "profit_margin": sale.profit_margin,
    }
    
    return sale_dict