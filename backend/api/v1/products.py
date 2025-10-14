from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from typing import List, Optional

from backend.database.base import get_db
from backend.api.dependencies import get_current_active_user, get_admin_user, get_analyst_or_admin_user
from backend.schemas.products import ProductCreate, ProductUpdate, ProductResponse, ProductCategoryCreate, ProductCategoryResponse
from backend.models.products import Product, ProductCategory
from backend.models.user import User

router = APIRouter()

# Product Category endpoints
@router.post("/categories", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_product_category(
    category: ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new product category (Admin only)"""
    
    # Check if category already exists
    if db.query(ProductCategory).filter(ProductCategory.name == category.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product category already exists"
        )
    
    db_category = ProductCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category


@router.get("/categories", response_model=List[ProductCategoryResponse])
async def get_product_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all product categories"""
    
    categories = db.query(ProductCategory)\
        .filter(ProductCategory.is_active == True)\
        .order_by(ProductCategory.name)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return categories


# Product endpoints
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new product (Admin only)"""
    
    # Check if product code already exists
    if db.query(Product).filter(Product.code == product.code).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product code already exists"
        )
    
    # Verify category exists
    if not db.query(ProductCategory).filter(ProductCategory.id == product.category_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product category not found"
        )
    
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Load with category
    db_product = db.query(Product)\
        .options(joinedload(Product.category))\
        .filter(Product.id == db_product.id)\
        .first()
    
    return _enrich_product_response(db_product)


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, code, or brand"),
    category_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get products with filtering and search"""
    
    query = db.query(Product)\
        .options(joinedload(Product.category))\
        .filter(Product.is_active == True)
    
    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_filter),
                Product.code.ilike(search_filter),
                Product.brand.ilike(search_filter),
                Product.active_ingredient.ilike(search_filter)
            )
        )
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if is_active is not None:
        query = query.filter(Product.is_available == is_active)
    
    # Get total count and paginate
    products = query.order_by(Product.name)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return [_enrich_product_response(product) for product in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific product by ID"""
    
    product = db.query(Product)\
        .options(joinedload(Product.category))\
        .filter(Product.id == product_id, Product.is_active == True)\
        .first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return _enrich_product_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update a product (Admin only)"""
    
    db_product = db.query(Product)\
        .filter(Product.id == product_id, Product.is_active == True)\
        .first()
    
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if code is being updated and already exists
    update_data = product_update.dict(exclude_unset=True)
    if 'code' in update_data and update_data['code'] != db_product.code:
        existing_product = db.query(Product)\
            .filter(Product.code == update_data['code'], Product.id != product_id)\
            .first()
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product code already exists"
            )
    
    # Update fields
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    
    # Load with category
    db_product = db.query(Product)\
        .options(joinedload(Product.category))\
        .filter(Product.id == db_product.id)\
        .first()
    
    return _enrich_product_response(db_product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Soft delete a product (Admin only)"""
    
    product = db.query(Product)\
        .filter(Product.id == product_id, Product.is_active == True)\
        .first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product.is_active = False
    db.commit()


@router.get("/search/suggestions")
async def get_product_suggestions(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product suggestions for autocomplete"""
    
    search_filter = f"%{query}%"
    
    products = db.query(Product)\
        .filter(
            Product.is_active == True,
            Product.is_available == True,
            or_(
                Product.name.ilike(search_filter),
                Product.code.ilike(search_filter),
                Product.brand.ilike(search_filter)
            )
        )\
        .order_by(Product.name)\
        .limit(limit)\
        .all()
    
    return [
        {
            "id": product.id,
            "code": product.code,
            "name": product.name,
            "brand": product.brand,
            "full_description": product.full_description,
            "unit_price": product.unit_price
        }
        for product in products
    ]


def _enrich_product_response(product: Product) -> dict:
    """Enrich product response with additional data"""
    return {
        "id": product.id,
        "code": product.code,
        "name": product.name,
        "brand": product.brand,
        "manufacturer": product.manufacturer,
        "description": product.description,
        "active_ingredient": product.active_ingredient,
        "dosage": product.dosage,
        "package_size": product.package_size,
        "unit_price": product.unit_price,
        "suggested_retail_price": product.suggested_retail_price,
        "cost_price": product.cost_price,
        "category_id": product.category_id,
        "therapeutic_class": product.therapeutic_class,
        "controlled_substance": product.controlled_substance,
        "prescription_required": product.prescription_required,
        "ndc_number": product.ndc_number,
        "approval_date": product.approval_date,
        "expiry_monitoring": product.expiry_monitoring,
        "is_active": product.is_active,
        "is_available": product.is_available,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        
        # Related data
        "category_name": product.category.name if product.category else None,
        "full_description": product.full_description
    }