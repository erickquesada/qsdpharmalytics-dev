from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class AnalyticsCache(BaseModel):
    """Cache para resultados de analytics"""
    __tablename__ = "analytics_cache"
    
    cache_key = Column(String(255), unique=True, index=True, nullable=False)
    cache_type = Column(String(50), nullable=False)  # sales_performance, market_share, etc
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    parameters = Column(JSON, nullable=True)  # Parâmetros da query
    result_data = Column(JSON, nullable=False)  # Dados do resultado
    expires_at = Column(DateTime, nullable=True)  # Expiração do cache

class KPI(BaseModel):
    """Indicadores chave de performance"""
    __tablename__ = "kpis"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # sales, financial, operational
    calculation_method = Column(Text, nullable=True)
    target_value = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)  # %, R$, unidades
    frequency = Column(String(20), nullable=False, default="daily")  # daily, weekly, monthly

class KPIValue(BaseModel):
    """Valores históricos dos KPIs"""
    __tablename__ = "kpi_values"
    
    kpi_id = Column(Integer, ForeignKey("kpis.id"), nullable=False)
    date = Column(Date, nullable=False)
    value = Column(Float, nullable=False)
    target = Column(Float, nullable=True)
    variance = Column(Float, nullable=True)  # Diferença do target
    notes = Column(Text, nullable=True)
    
    # Relationship
    kpi = relationship("KPI", backref="values")

class Alert(BaseModel):
    """Alertas do sistema"""
    __tablename__ = "alerts"
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    alert_type = Column(String(50), nullable=False)  # warning, critical, info
    category = Column(String(50), nullable=False)  # sales, inventory, performance
    trigger_condition = Column(Text, nullable=True)
    threshold_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)

class Dashboard(BaseModel):
    """Configurações de dashboards personalizados"""
    __tablename__ = "dashboards"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    layout_config = Column(JSON, nullable=True)  # Configuração do layout
    widgets = Column(JSON, nullable=True)  # Lista de widgets
    is_default = Column(Boolean, default=False)
    created_by = Column(String(100), nullable=True)

class ReportTemplate(BaseModel):
    """Templates de relatórios"""
    __tablename__ = "report_templates"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String(50), nullable=False)  # pdf, excel, csv
    template_config = Column(JSON, nullable=False)  # Configuração do template
    default_parameters = Column(JSON, nullable=True)
    is_system = Column(Boolean, default=False)  # Template do sistema ou personalizado

class DataSource(BaseModel):
    """Fontes de dados externas"""
    __tablename__ = "data_sources"
    
    name = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)  # api, file, database
    connection_config = Column(JSON, nullable=True)
    sync_frequency = Column(String(20), nullable=True)  # hourly, daily, weekly
    last_sync = Column(DateTime, nullable=True)
    sync_status = Column(String(20), default="pending")  # pending, running, success, error
    error_message = Column(Text, nullable=True)