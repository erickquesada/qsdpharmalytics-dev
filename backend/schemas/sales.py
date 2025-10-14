from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from backend.models.sales import PaymentMethod, SaleStatus


class SaleBase(BaseModel):
    product_id: int
    pharmacy_id: int
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    discount_amount: Optional[Decimal] = Field(0, ge=0)
    tax_amount: Optional[Decimal] = Field(0, ge=0)
    payment_method: PaymentMethod = PaymentMethod.NET_TERMS
    status: SaleStatus = SaleStatus.PENDING
    sale_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    order_number: Optional[str] = None
    po_number: Optional[str] = None
    campaign_id: Optional[str] = None
    promotion_code: Optional[str] = None
    territory: Optional[str] = None
    region: Optional[str] = None
    notes: Optional[str] = None


class SaleCreate(SaleBase):
    sales_rep_id: Optional[int] = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v


class SaleUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, gt=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    payment_method: Optional[PaymentMethod] = None
    status: Optional[SaleStatus] = None
    delivery_date: Optional[datetime] = None
    po_number: Optional[str] = None
    notes: Optional[str] = None


class SaleResponse(SaleBase):
    id: int
    total_price: Decimal
    final_amount: Decimal
    invoice_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    pharmacy_name: Optional[str] = None
    pharmacy_location: Optional[str] = None
    sales_rep_name: Optional[str] = None
    
    # Calculated fields
    discount_percentage: Optional[float] = None
    profit_margin: Optional[float] = None
    
    class Config:
        from_attributes = True


class SaleListResponse(BaseModel):
    items: List[SaleResponse]
    total: int
    page: int
    size: int
    pages: int


class SalesSummary(BaseModel):
    total_sales: int
    total_revenue: Decimal
    total_quantity: int
    average_order_value: Decimal
    top_product: Optional[str] = None
    top_pharmacy: Optional[str] = None
    period_start: datetime
    period_end: datetime


class SalesFilters(BaseModel):
    product_id: Optional[int] = None
    pharmacy_id: Optional[int] = None
    sales_rep_id: Optional[int] = None
    status: Optional[SaleStatus] = None
    payment_method: Optional[PaymentMethod] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    territory: Optional[str] = None
    region: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None