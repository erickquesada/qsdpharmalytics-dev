from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal

# Base Schemas
class SaleBase(BaseModel):
    product_name: str
    product_category: str
    product_code: str
    quantity: int
    unit_price: float
    discount: Optional[float] = 0.0
    pharmacy_name: Optional[str] = None
    pharmacy_location: Optional[str] = None
    customer_type: Optional[str] = None
    payment_method: Optional[str] = None
    campaign_id: Optional[str] = None
    sales_rep: Optional[str] = None
    notes: Optional[str] = None

class SaleCreate(SaleBase):
    sale_date: Optional[datetime] = None
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantidade deve ser positiva')
        return v
    
    @validator('unit_price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Preço deve ser positivo')
        return v

class SaleUpdate(BaseModel):
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    discount: Optional[float] = None
    pharmacy_name: Optional[str] = None
    pharmacy_location: Optional[str] = None
    customer_type: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None

class Sale(SaleBase):
    id: int
    total_price: float
    sale_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    name: str
    code: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    unit_cost: Optional[float] = None
    suggested_price: Optional[float] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    unit_cost: Optional[float] = None
    suggested_price: Optional[float] = None

class Product(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Pharmacy Schemas
class PharmacyBase(BaseModel):
    name: str
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    type: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class PharmacyCreate(PharmacyBase):
    pass

class PharmacyUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    type: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class Pharmacy(PharmacyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Response Schemas
class SalesResponse(BaseModel):
    sales: list[Sale]
    total: int
    page: int
    per_page: int

class MessageResponse(BaseModel):
    message: str
    success: bool = True