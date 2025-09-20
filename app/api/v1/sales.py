from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List
from datetime import datetime, date

from app.database import get_db
from app.models.sales import Sale, Product, Pharmacy
from app.schemas.sales import (
    SaleCreate, SaleUpdate, Sale as SaleSchema,
    ProductCreate, ProductUpdate, Product as ProductSchema,
    PharmacyCreate, PharmacyUpdate, Pharmacy as PharmacySchema,
    SalesResponse, MessageResponse
)

router = APIRouter()

# ========== SALES ENDPOINTS ==========

@router.post("/", response_model=SaleSchema)
async def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    """Criar nova venda"""
    # Calcular total
    total_price = (sale.quantity * sale.unit_price) - (sale.discount or 0)
    
    db_sale = Sale(
        **sale.dict(exclude={'sale_date'}),
        total_price=total_price,
        sale_date=sale.sale_date or datetime.now()
    )
    
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    return db_sale

@router.get("/", response_model=SalesResponse)
async def get_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    product_name: Optional[str] = None,
    category: Optional[str] = None,
    pharmacy: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Listar vendas com filtros"""
    query = db.query(Sale).filter(Sale.is_active == True)
    
    # Aplicar filtros
    if product_name:
        query = query.filter(Sale.product_name.ilike(f"%{product_name}%"))
    
    if category:
        query = query.filter(Sale.product_category.ilike(f"%{category}%"))
    
    if pharmacy:
        query = query.filter(Sale.pharmacy_name.ilike(f"%{pharmacy}%"))
    
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    
    # Contar total
    total = query.count()
    
    # Paginação e ordenação
    sales = query.order_by(desc(Sale.sale_date)).offset(skip).limit(limit).all()
    
    return SalesResponse(
        sales=sales,
        total=total,
        page=(skip // limit) + 1,
        per_page=limit
    )

@router.get("/{sale_id}", response_model=SaleSchema)
async def get_sale(sale_id: int, db: Session = Depends(get_db)):
    """Obter detalhes de uma venda"""
    sale = db.query(Sale).filter(
        Sale.id == sale_id, 
        Sale.is_active == True
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    return sale

@router.put("/{sale_id}", response_model=SaleSchema)
async def update_sale(
    sale_id: int, 
    sale_update: SaleUpdate, 
    db: Session = Depends(get_db)
):
    """Atualizar venda"""
    sale = db.query(Sale).filter(
        Sale.id == sale_id, 
        Sale.is_active == True
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    # Atualizar campos
    update_data = sale_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sale, field, value)
    
    # Recalcular total se necessário
    if any(field in update_data for field in ['quantity', 'unit_price', 'discount']):
        sale.total_price = (sale.quantity * sale.unit_price) - (sale.discount or 0)
    
    sale.updated_at = datetime.now()
    
    db.commit()
    db.refresh(sale)
    
    return sale

@router.delete("/{sale_id}", response_model=MessageResponse)
async def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    """Excluir venda (soft delete)"""
    sale = db.query(Sale).filter(
        Sale.id == sale_id, 
        Sale.is_active == True
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    sale.is_active = False
    sale.updated_at = datetime.now()
    
    db.commit()
    
    return MessageResponse(message="Venda excluída com sucesso")

# ========== PRODUCTS ENDPOINTS ==========

@router.post("/products/", response_model=ProductSchema)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Criar novo produto"""
    # Verificar se código já existe
    existing = db.query(Product).filter(Product.code == product.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Código do produto já existe")
    
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product

@router.get("/products/", response_model=List[ProductSchema])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar produtos"""
    query = db.query(Product).filter(Product.is_active == True)
    
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    
    products = query.offset(skip).limit(limit).all()
    return products

# ========== PHARMACIES ENDPOINTS ==========

@router.post("/pharmacies/", response_model=PharmacySchema)
async def create_pharmacy(pharmacy: PharmacyCreate, db: Session = Depends(get_db)):
    """Criar nova farmácia"""
    db_pharmacy = Pharmacy(**pharmacy.dict())
    db.add(db_pharmacy)
    db.commit()
    db.refresh(db_pharmacy)
    
    return db_pharmacy

@router.get("/pharmacies/", response_model=List[PharmacySchema])
async def get_pharmacies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar farmácias"""
    query = db.query(Pharmacy).filter(Pharmacy.is_active == True)
    
    if city:
        query = query.filter(Pharmacy.city.ilike(f"%{city}%"))
    
    pharmacies = query.offset(skip).limit(limit).all()
    return pharmacies