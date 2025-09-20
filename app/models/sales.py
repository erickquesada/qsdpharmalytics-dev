from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Informações do produto
    product_name = Column(String(255), nullable=False, index=True)
    product_category = Column(String(100), nullable=False, index=True)
    product_code = Column(String(50), unique=True, index=True)
    
    # Informações da venda
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    
    # Informações do cliente/farmácia
    pharmacy_name = Column(String(255))
    pharmacy_location = Column(String(255))
    customer_type = Column(String(50))  # retail, wholesale, hospital, etc.
    
    # Informações da transação
    sale_date = Column(DateTime, nullable=False, default=func.now())
    payment_method = Column(String(50))
    
    # Informações de marketing/campanha
    campaign_id = Column(String(50))
    sales_rep = Column(String(100))
    
    # Metadados
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100))
    
    # Informações do produto
    description = Column(Text)
    manufacturer = Column(String(200))
    unit_cost = Column(Float)
    suggested_price = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Pharmacy(Base):
    __tablename__ = "pharmacies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    location = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    type = Column(String(50))  # chain, independent, hospital
    
    # Informações de contato
    contact_person = Column(String(200))
    phone = Column(String(20))
    email = Column(String(200))
    
    # Metadados
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())