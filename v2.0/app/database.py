from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import time
import logging

from app.core.config import settings

# Configurar logging do SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(
    logging.DEBUG if settings.DEBUG else logging.INFO
)

# Configurações específicas para PostgreSQL vs SQLite
def get_engine_config():
    """Retornar configurações específicas do engine baseado no tipo de banco"""
    
    if settings.database_url.startswith('postgresql://'):
        # Configurações PostgreSQL
        return {
            'poolclass': QueuePool,
            'pool_size': 20,
            'max_overflow': 0,
            'pool_pre_ping': True,
            'pool_recycle': 3600,  # 1 hora
            'connect_args': {
                'connect_timeout': 60,
                'application_name': 'QSDPharmalitics_API',
            },
            'echo': settings.DEBUG,
            'echo_pool': settings.DEBUG,
        }
    else:
        # Configurações SQLite (desenvolvimento)
        return {
            'connect_args': {
                'check_same_thread': False,
                'timeout': 30
            },
            'echo': settings.DEBUG,
            'pool_pre_ping': True,
        }

# Criar engine com configurações otimizadas
engine_config = get_engine_config()
engine = create_engine(settings.database_url, **engine_config)

# Event listeners para otimizações
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Otimizações específicas para SQLite"""
    if 'sqlite' in settings.database_url:
        cursor = dbapi_connection.cursor()
        # Otimizações de performance
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        cursor.close()

@event.listens_for(Engine, "connect")
def set_postgresql_config(dbapi_connection, connection_record):
    """Configurações específicas para PostgreSQL"""
    if 'postgresql' in settings.database_url:
        with dbapi_connection.cursor() as cursor:
            # Timezone
            cursor.execute("SET timezone = 'America/Sao_Paulo'")
            
            # Configurações de performance para analytics
            cursor.execute("SET work_mem = '256MB'")
            cursor.execute("SET maintenance_work_mem = '512MB'")
            cursor.execute("SET effective_cache_size = '4GB'")
            cursor.execute("SET random_page_cost = 1.1")
            
            # Configurações para relatórios
            cursor.execute("SET enable_hashagg = on")
            cursor.execute("SET enable_sort = on")

# Session maker
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Importante para analytics
)

# Base para os modelos
Base = declarative_base()

# Dependency para obter sessão do banco
def get_db():
    """Dependency para obter sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        db.close()

# Função para testar conexão
def test_database_connection():
    """Testar conexão com o banco de dados"""
    try:
        with engine.connect() as connection:
            if 'postgresql' in settings.database_url:
                result = connection.execute("SELECT version()")
                version = result.fetchone()[0]
                print(f"✅ PostgreSQL conectado: {version}")
            else:
                result = connection.execute("SELECT sqlite_version()")
                version = result.fetchone()[0]
                print(f"✅ SQLite conectado: {version}")
        
        return True
    except Exception as e:
        print(f"❌ Erro na conexão com banco: {e}")
        return False

# Função para criar todas as tabelas
def create_tables():
    """Criar todas as tabelas no banco"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

# Context manager para transações
class DatabaseTransaction:
    """Context manager para transações de banco"""
    
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db.rollback()
            logging.error(f"Transaction rolled back: {exc_val}")
        else:
            self.db.commit()
        
        self.db.close()

# Função utilitária para queries analíticas
def execute_analytics_query(query, params=None):
    """Executar query analítica com otimizações"""
    
    with SessionLocal() as db:
        try:
            # Para PostgreSQL, usar configurações específicas para analytics
            if 'postgresql' in settings.database_url:
                db.execute("SET statement_timeout = '5min'")
                db.execute("SET work_mem = '512MB'")
            
            result = db.execute(query, params or {})
            return result.fetchall()
            
        except Exception as e:
            logging.error(f"Analytics query error: {e}")
            raise

# Monitoramento de performance
class QueryPerformanceMonitor:
    """Monitor de performance de queries"""
    
    def __init__(self, query_name: str):
        self.query_name = query_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            if duration > 1.0:  # Queries > 1 segundo
                logging.warning(f"Slow query '{self.query_name}': {duration:.2f}s")
            elif settings.DEBUG:
                logging.debug(f"Query '{self.query_name}': {duration:.3f}s")

# Health check do banco
def database_health_check():
    """Verificar saúde do banco de dados"""
    
    health_info = {
        "database_type": "postgresql" if "postgresql" in settings.database_url else "sqlite",
        "connection_status": "unknown",
        "response_time_ms": None,
        "active_connections": None,
        "error": None
    }
    
    start_time = time.time()
    
    try:
        with engine.connect() as connection:
            # Teste de conectividade
            if 'postgresql' in settings.database_url:
                # PostgreSQL específico
                result = connection.execute("""
                    SELECT 
                        COUNT(*) as active_connections,
                        current_database() as database_name,
                        version() as version
                """)
                row = result.fetchone()
                health_info["active_connections"] = row[0]
                health_info["database_name"] = row[1]
                health_info["version"] = row[2][:50] + "..." if len(row[2]) > 50 else row[2]
            else:
                # SQLite específico  
                result = connection.execute("SELECT sqlite_version()")
                version = result.fetchone()[0]
                health_info["version"] = f"SQLite {version}"
            
            health_info["connection_status"] = "healthy"
            health_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            
    except Exception as e:
        health_info["connection_status"] = "error"
        health_info["error"] = str(e)
        health_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return health_info