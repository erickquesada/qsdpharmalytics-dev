from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database.base import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    products = relationship("Product", back_populates="category")
    parent = relationship("ProductCategory", remote_side=[id], backref="subcategories")
    
    def __repr__(self):
        return f"<ProductCategory(id={self.id}, name={self.name})>"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    brand = Column(String(100), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    
    # Product Details
    description = Column(Text, nullable=True)
    active_ingredient = Column(String(255), nullable=True)
    dosage = Column(String(100), nullable=True)
    package_size = Column(String(50), nullable=True)
    
    # Pricing
    unit_price = Column(Numeric(10, 2), nullable=True)
    suggested_retail_price = Column(Numeric(10, 2), nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=True)
    
    # Classification
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=False)
    therapeutic_class = Column(String(100), nullable=True)
    controlled_substance = Column(Boolean, default=False)
    prescription_required = Column(Boolean, default=False)
    
    # Regulatory
    ndc_number = Column(String(20), nullable=True)  # National Drug Code
    approval_date = Column(DateTime(timezone=True), nullable=True)
    expiry_monitoring = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    sales = relationship("Sale", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, code={self.code}, name={self.name})>"
    
    @property
    def category_name(self):
        return self.category.name if self.category else None
    
    @property
    def full_description(self):
        parts = [self.name]
        if self.dosage:
            parts.append(f"({self.dosage})")
        if self.package_size:
            parts.append(f"- {self.package_size}")
        return " ".join(parts)