from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from backend.models.pharmacies import PharmacyType, CustomerType


class PharmacyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="USA", max_length=50)
    pharmacy_type: PharmacyType = PharmacyType.INDEPENDENT
    customer_type: CustomerType = CustomerType.RETAIL
    chain_name: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    dea_number: Optional[str] = Field(None, max_length=20)
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=50)
    discount_tier: Optional[str] = Field(None, max_length=20)
    market_segment: Optional[str] = Field(None, max_length=50)
    territory: Optional[str] = Field(None, max_length=50)
    population_density: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class PharmacyCreate(PharmacyBase):
    pass


class PharmacyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    address_line1: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=50)
    pharmacy_type: Optional[PharmacyType] = None
    customer_type: Optional[CustomerType] = None
    chain_name: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    dea_number: Optional[str] = Field(None, max_length=20)
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=50)
    discount_tier: Optional[str] = Field(None, max_length=20)
    market_segment: Optional[str] = Field(None, max_length=50)
    territory: Optional[str] = Field(None, max_length=50)
    population_density: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class PharmacyResponse(PharmacyBase):
    id: int
    annual_volume: Decimal
    average_order_value: Decimal
    last_order_date: Optional[datetime] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    full_address: Optional[str] = None
    location: Optional[str] = None
    
    class Config:
        from_attributes = True