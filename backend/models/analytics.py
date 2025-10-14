from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, JSON, Enum, Numeric
from sqlalchemy.sql import func
import enum
from backend.database.base import Base


class MetricType(str, enum.Enum):
    DAILY_SALES = "daily_sales"
    WEEKLY_SALES = "weekly_sales"
    MONTHLY_SALES = "monthly_sales"
    QUARTERLY_SALES = "quarterly_sales"
    YEARLY_SALES = "yearly_sales"
    PRODUCT_PERFORMANCE = "product_performance"
    PHARMACY_PERFORMANCE = "pharmacy_performance"
    TERRITORY_PERFORMANCE = "territory_performance"


class ReportType(str, enum.Enum):
    SALES_SUMMARY = "sales_summary"
    MONTHLY_REPORT = "monthly_report"
    QUARTERLY_REPORT = "quarterly_report"
    ANNUAL_REPORT = "annual_report"
    PRODUCT_ANALYSIS = "product_analysis"
    MARKET_SHARE = "market_share"
    PERFORMANCE_DASHBOARD = "performance_dashboard"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


class SalesMetric(Base):
    __tablename__ = "sales_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Metric Identification
    metric_type = Column(Enum(MetricType), nullable=False, index=True)
    metric_date = Column(Date, nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Dimensional Data
    product_id = Column(Integer, nullable=True, index=True)
    product_category_id = Column(Integer, nullable=True, index=True)
    pharmacy_id = Column(Integer, nullable=True, index=True)
    territory = Column(String(50), nullable=True, index=True)
    region = Column(String(50), nullable=True, index=True)
    
    # Metric Values
    total_revenue = Column(Numeric(15, 2), default=0.00)
    total_quantity = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    unique_customers = Column(Integer, default=0)
    
    # Calculated Metrics
    average_order_value = Column(Numeric(10, 2), default=0.00)
    average_selling_price = Column(Numeric(10, 2), default=0.00)
    gross_margin = Column(Numeric(10, 4), default=0.00)  # Percentage
    market_share = Column(Numeric(8, 4), default=0.00)    # Percentage
    
    # Growth Metrics
    revenue_growth = Column(Numeric(8, 4), default=0.00)   # Percentage vs previous period
    quantity_growth = Column(Numeric(8, 4), default=0.00)  # Percentage vs previous period
    
    # Additional Data
    additional_data = Column(JSON, nullable=True)
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SalesMetric(id={self.id}, type={self.metric_type}, date={self.metric_date})>"


class MarketShareData(Base):
    __tablename__ = "market_share_data"

    id = Column(Integer, primary_key=True, index=True)
    
    # Time Period
    analysis_date = Column(Date, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    
    # Market Segmentation
    market_category = Column(String(100), nullable=False, index=True)
    product_category = Column(String(100), nullable=True, index=True)
    geographic_region = Column(String(50), nullable=True, index=True)
    
    # Market Data
    total_market_size = Column(Numeric(15, 2), nullable=False)
    our_revenue = Column(Numeric(15, 2), nullable=False)
    market_share_percentage = Column(Numeric(8, 4), nullable=False)
    
    # Competitive Analysis
    competitor_count = Column(Integer, default=0)
    market_rank = Column(Integer, nullable=True)
    
    # Trends
    previous_period_share = Column(Numeric(8, 4), nullable=True)
    share_change = Column(Numeric(8, 4), nullable=True)
    
    # Additional Data
    analysis_notes = Column(Text, nullable=True)
    data_sources = Column(JSON, nullable=True)
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<MarketShareData(id={self.id}, category={self.market_category}, share={self.market_share_percentage}%)>"


class TrendAnalysis(Base):
    __tablename__ = "trend_analysis"

    id = Column(Integer, primary_key=True, index=True)
    
    # Analysis Identification
    analysis_name = Column(String(255), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # sales_trend, seasonal, forecast
    
    # Time Scope
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    analysis_date = Column(Date, nullable=False, index=True)
    
    # Scope Filters
    product_filter = Column(JSON, nullable=True)
    pharmacy_filter = Column(JSON, nullable=True)
    geographic_filter = Column(JSON, nullable=True)
    
    # Trend Results
    trend_direction = Column(String(20), nullable=True)  # increasing, decreasing, stable, volatile
    trend_strength = Column(Numeric(5, 4), nullable=True)  # correlation coefficient
    seasonal_pattern = Column(Boolean, default=False)
    
    # Statistical Data
    trend_data = Column(JSON, nullable=False)  # Time series data
    regression_coefficients = Column(JSON, nullable=True)
    statistical_measures = Column(JSON, nullable=True)  # R-squared, p-values, etc.
    
    # Predictions (if applicable)
    forecast_data = Column(JSON, nullable=True)
    confidence_intervals = Column(JSON, nullable=True)
    
    # Analysis Metadata
    methodology = Column(String(100), nullable=True)
    data_quality_score = Column(Numeric(3, 2), nullable=True)
    analysis_notes = Column(Text, nullable=True)
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<TrendAnalysis(id={self.id}, name={self.analysis_name}, direction={self.trend_direction})>"


class ReportGeneration(Base):
    __tablename__ = "report_generations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Report Identification
    report_name = Column(String(255), nullable=False)
    report_type = Column(Enum(ReportType), nullable=False)
    format_type = Column(String(20), nullable=False)  # pdf, excel, csv
    
    # Generation Details
    generated_by_user_id = Column(Integer, nullable=False)
    generation_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Report Scope
    date_range_start = Column(Date, nullable=False)
    date_range_end = Column(Date, nullable=False)
    filters_applied = Column(JSON, nullable=True)
    
    # File Information
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)  # in bytes
    download_count = Column(Integer, default=0)
    
    # Report Metadata
    total_records = Column(Integer, default=0)
    generation_duration = Column(Numeric(8, 3), nullable=True)  # seconds
    
    # Status
    status = Column(String(20), default="completed")  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<ReportGeneration(id={self.id}, type={self.report_type}, status={self.status})>"