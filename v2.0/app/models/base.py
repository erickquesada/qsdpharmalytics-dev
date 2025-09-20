from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class BaseModel(Base):
    """Modelo base com campos comuns"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class TimestampMixin:
    """Mixin para timestamps"""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class SoftDeleteMixin:
    """Mixin para soft delete"""
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

class AuditMixin:
    """Mixin para auditoria"""
    created_by = Column(Integer, nullable=True)  # ID do usuário que criou
    updated_by = Column(Integer, nullable=True)  # ID do usuário que atualizou