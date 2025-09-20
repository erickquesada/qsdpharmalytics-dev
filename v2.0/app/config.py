import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Informações da aplicação
    APP_NAME: str = "QSDPharmalitics"
    APP_VERSION: str = "2.0.0"
    
    # Banco de dados
    DATABASE_URL: str = "sqlite:///./pharmalitics.db"
    
    # Configurações da API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    # Configurações de desenvolvimento
    DEBUG: bool = True
    
    # Configurações de CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Configurações de relatórios
    REPORTS_DIR: str = "./reports"
    
    # Configurações de timezone
    TIMEZONE: str = "America/Sao_Paulo"
    
    # Configurações do banco PostgreSQL (opcional)
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_PORT: Optional[str] = "5432"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        """Retorna URL do banco de dados baseado nas configurações"""
        if all([
            self.POSTGRES_SERVER, 
            self.POSTGRES_USER, 
            self.POSTGRES_PASSWORD, 
            self.POSTGRES_DB
        ]):
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return self.DATABASE_URL

# Instância global das configurações
settings = Settings()