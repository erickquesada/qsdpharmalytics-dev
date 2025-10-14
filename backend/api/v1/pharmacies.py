from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import List, Optional

from backend.database.base import get_db
from backend.api.dependencies import get_current_active_user, get_admin_user
from backend.schemas.pharmacies import PharmacyCreate, PharmacyUpdate, PharmacyResponse
from backend.models.pharmacies import Pharmacy, PharmacyType, CustomerType
from backend.models.user import User

router = APIRouter()


@router.post("/", response_model=PharmacyResponse, status_code=status.HTTP_201_CREATED)
async def create_pharmacy(
    pharmacy: PharmacyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new pharmacy (Admin only)"""
    
    # Check if pharmacy code already exists (if provided)
    if pharmacy.code and db.query(Pharmacy).filter(Pharmacy.code == pharmacy.code).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pharmacy code already exists"
        )
    
    db_pharmacy = Pharmacy(**pharmacy.dict())
    db.add(db_pharmacy)
    db.commit()
    db.refresh(db_pharmacy)
    
    return _enrich_pharmacy_response(db_pharmacy)


@router.get("/", response_model=List[PharmacyResponse])
async def get_pharmacies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, city, or code"),
    pharmacy_type: Optional[PharmacyType] = None,
    customer_type: Optional[CustomerType] = None,
    state: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get pharmacies with filtering and search"""
    
    query = db.query(Pharmacy).filter(Pharmacy.is_active == True)
    
    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Pharmacy.name.ilike(search_filter),
                Pharmacy.code.ilike(search_filter),
                Pharmacy.city.ilike(search_filter),
                Pharmacy.chain_name.ilike(search_filter)
            )
        )
    
    if pharmacy_type:
        query = query.filter(Pharmacy.pharmacy_type == pharmacy_type)
    
    if customer_type:
        query = query.filter(Pharmacy.customer_type == customer_type)
    
    if state:
        query = query.filter(Pharmacy.state.ilike(f"%{state}%"))
    
    if is_active is not None:
        query = query.filter(Pharmacy.is_active == is_active)
    
    # Get pharmacies with pagination
    pharmacies = query.order_by(Pharmacy.name)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return [_enrich_pharmacy_response(pharmacy) for pharmacy in pharmacies]


@router.get("/{pharmacy_id}", response_model=PharmacyResponse)
async def get_pharmacy(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific pharmacy by ID"""
    
    pharmacy = db.query(Pharmacy)\
        .filter(Pharmacy.id == pharmacy_id, Pharmacy.is_active == True)\
        .first()
    
    if not pharmacy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pharmacy not found"
        )
    
    return _enrich_pharmacy_response(pharmacy)


@router.put("/{pharmacy_id}", response_model=PharmacyResponse)
async def update_pharmacy(
    pharmacy_id: int,
    pharmacy_update: PharmacyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update a pharmacy (Admin only)"""
    
    db_pharmacy = db.query(Pharmacy)\
        .filter(Pharmacy.id == pharmacy_id, Pharmacy.is_active == True)\
        .first()
    
    if not db_pharmacy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pharmacy not found"
        )
    
    # Check if code is being updated and already exists
    update_data = pharmacy_update.dict(exclude_unset=True)
    if 'code' in update_data and update_data['code'] != db_pharmacy.code:
        existing_pharmacy = db.query(Pharmacy)\
            .filter(Pharmacy.code == update_data['code'], Pharmacy.id != pharmacy_id)\
            .first()
        if existing_pharmacy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pharmacy code already exists"
            )
    
    # Update fields
    for field, value in update_data.items():
        setattr(db_pharmacy, field, value)
    
    db.commit()
    db.refresh(db_pharmacy)
    
    return _enrich_pharmacy_response(db_pharmacy)


@router.delete("/{pharmacy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pharmacy(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Soft delete a pharmacy (Admin only)"""
    
    pharmacy = db.query(Pharmacy)\
        .filter(Pharmacy.id == pharmacy_id, Pharmacy.is_active == True)\
        .first()
    
    if not pharmacy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pharmacy not found"
        )
    
    pharmacy.is_active = False
    db.commit()


@router.get("/search/suggestions")
async def get_pharmacy_suggestions(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get pharmacy suggestions for autocomplete"""
    
    search_filter = f"%{query}%"
    
    pharmacies = db.query(Pharmacy)\
        .filter(
            Pharmacy.is_active == True,
            or_(
                Pharmacy.name.ilike(search_filter),
                Pharmacy.code.ilike(search_filter),
                Pharmacy.city.ilike(search_filter)
            )
        )\
        .order_by(Pharmacy.name)\
        .limit(limit)\
        .all()
    
    return [
        {
            "id": pharmacy.id,
            "code": pharmacy.code,
            "name": pharmacy.name,
            "location": pharmacy.location,
            "pharmacy_type": pharmacy.pharmacy_type,
            "customer_type": pharmacy.customer_type
        }
        for pharmacy in pharmacies
    ]


def _enrich_pharmacy_response(pharmacy: Pharmacy) -> dict:
    """Enrich pharmacy response with additional data"""
    return {
        "id": pharmacy.id,
        "name": pharmacy.name,
        "code": pharmacy.code,
        "email": pharmacy.email,
        "phone": pharmacy.phone,
        "fax": pharmacy.fax,
        "website": pharmacy.website,
        "address_line1": pharmacy.address_line1,
        "address_line2": pharmacy.address_line2,
        "city": pharmacy.city,
        "state": pharmacy.state,
        "zip_code": pharmacy.zip_code,
        "country": pharmacy.country,
        "pharmacy_type": pharmacy.pharmacy_type,
        "customer_type": pharmacy.customer_type,
        "chain_name": pharmacy.chain_name,
        "license_number": pharmacy.license_number,
        "dea_number": pharmacy.dea_number,
        "credit_limit": pharmacy.credit_limit,
        "payment_terms": pharmacy.payment_terms,
        "discount_tier": pharmacy.discount_tier,
        "market_segment": pharmacy.market_segment,
        "territory": pharmacy.territory,
        "population_density": pharmacy.population_density,
        "annual_volume": pharmacy.annual_volume,
        "average_order_value": pharmacy.average_order_value,
        "last_order_date": pharmacy.last_order_date,
        "notes": pharmacy.notes,
        "is_active": pharmacy.is_active,
        "is_verified": pharmacy.is_verified,
        "created_at": pharmacy.created_at,
        "updated_at": pharmacy.updated_at,
        
        # Computed fields
        "full_address": pharmacy.full_address,
        "location": pharmacy.location,
    }