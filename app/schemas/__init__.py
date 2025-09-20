"""
Schemas Pydantic para validação de dados
"""

from .sales import (
    SaleCreate, SaleUpdate, Sale,
    ProductCreate, ProductUpdate, Product,
    PharmacyCreate, PharmacyUpdate, Pharmacy,
    SalesResponse, MessageResponse
)

from .analytics import (
    PerformanceData, MarketShareData, TrendData, TopProductData,
    CustomerAnalysisData, RevenueAnalysisData, SeasonalityData,
    GrowthAnalysis, ComparisonData, AnalyticsRequest,
    PerformanceRequest, MarketShareRequest, TrendsRequest,
    TopProductsRequest, CustomerAnalysisRequest, DashboardRequest,
    AnalyticsResponse, PerformanceResponse, MarketShareResponse,
    TrendsResponse, DashboardResponse, KPI, KPIValue, Alert,
    ExportRequest, ExportResponse
)

__all__ = [
    # Sales schemas
    "SaleCreate", "SaleUpdate", "Sale",
    "ProductCreate", "ProductUpdate", "Product", 
    "PharmacyCreate", "PharmacyUpdate", "Pharmacy",
    "SalesResponse", "MessageResponse",
    
    # Analytics schemas
    "PerformanceData", "MarketShareData", "TrendData", "TopProductData",
    "CustomerAnalysisData", "RevenueAnalysisData", "SeasonalityData", 
    "GrowthAnalysis", "ComparisonData", "AnalyticsRequest",
    "PerformanceRequest", "MarketShareRequest", "TrendsRequest",
    "TopProductsRequest", "CustomerAnalysisRequest", "DashboardRequest",
    "AnalyticsResponse", "PerformanceResponse", "MarketShareResponse",
    "TrendsResponse", "DashboardResponse", "KPI", "KPIValue", "Alert",
    "ExportRequest", "ExportResponse"
]