from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from backend.database.base import Base


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CHECK = "check"
    WIRE_TRANSFER = "wire_transfer"
    NET_TERMS = "net_terms"


class SaleStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False)
    sales_rep_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Sale Details
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    tax_amount = Column(Numeric(10, 2), default=0.00)
    final_amount = Column(Numeric(10, 2), nullable=False)
    
    # Transaction Information
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.NET_TERMS)
    status = Column(Enum(SaleStatus), default=SaleStatus.PENDING)
    sale_date = Column(DateTime(timezone=True), server_default=func.now())
    delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Reference Numbers
    order_number = Column(String(50), unique=True, nullable=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=True, index=True)
    po_number = Column(String(50), nullable=True)  # Purchase Order from customer
    
    # Campaign & Marketing
    campaign_id = Column(String(50), nullable=True)
    promotion_code = Column(String(20), nullable=True)
    referral_source = Column(String(100), nullable=True)
    
    # Geographic & Market Data
    territory = Column(String(50), nullable=True)
    region = Column(String(50), nullable=True)
    market_segment = Column(String(50), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="sales")
    pharmacy = relationship("Pharmacy", back_populates="sales")
    sales_rep = relationship("User", foreign_keys=[sales_rep_id])
    
    def __repr__(self):
        return f"<Sale(id={self.id}, product={self.product.name if self.product else 'N/A'}, amount={self.final_amount})>"
    
    @property
    def profit_margin(self):
        if self.product and self.product.cost_price:
            cost = float(self.product.cost_price) * self.quantity
            revenue = float(self.final_amount)
            return ((revenue - cost) / revenue) * 100 if revenue > 0 else 0
        return None
    
    @property
    def discount_percentage(self):
        if self.total_price > 0:
            return (float(self.discount_amount) / float(self.total_price)) * 100
        return 0
    
    def calculate_totals(self):
        """Calculate all monetary fields based on quantity and unit_price"""
        self.total_price = self.quantity * self.unit_price
        self.final_amount = self.total_price - self.discount_amount + self.tax_amount