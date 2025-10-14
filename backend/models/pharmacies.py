from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from backend.database.base import Base


class PharmacyType(str, enum.Enum):
    INDEPENDENT = "independent"
    CHAIN = "chain"
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    ONLINE = "online"


class CustomerType(str, enum.Enum):
    RETAIL = "retail"
    WHOLESALE = "wholesale"
    INSTITUTIONAL = "institutional"


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=True, index=True)
    
    # Contact Information
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    fax = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Address Information
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(50), default="USA", nullable=False)
    
    # Business Details
    pharmacy_type = Column(Enum(PharmacyType), default=PharmacyType.INDEPENDENT)
    customer_type = Column(Enum(CustomerType), default=CustomerType.RETAIL)
    chain_name = Column(String(100), nullable=True)
    license_number = Column(String(50), nullable=True)
    dea_number = Column(String(20), nullable=True)
    
    # Financial Information
    credit_limit = Column(Numeric(12, 2), default=0.00)
    payment_terms = Column(String(50), nullable=True)  # e.g., "Net 30"
    discount_tier = Column(String(20), nullable=True)  # e.g., "Premium", "Standard"
    
    # Geographic & Market Data
    market_segment = Column(String(50), nullable=True)
    territory = Column(String(50), nullable=True)
    population_density = Column(String(20), nullable=True)  # Urban, Suburban, Rural
    
    # Performance Metrics
    annual_volume = Column(Numeric(12, 2), default=0.00)
    average_order_value = Column(Numeric(10, 2), default=0.00)
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status & Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional Information
    notes = Column(Text, nullable=True)
    
    # Relationships
    sales = relationship("Sale", back_populates="pharmacy")
    
    def __repr__(self):
        return f"<Pharmacy(id={self.id}, name={self.name}, type={self.pharmacy_type})>"
    
    @property
    def full_address(self):
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.extend([self.city, self.state])
        if self.zip_code:
            parts.append(self.zip_code)
        return ", ".join(parts)
    
    @property
    def location(self):
        return f"{self.city}, {self.state}"