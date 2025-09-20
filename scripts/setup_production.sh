#!/bin/bash

# ================================
# SETUP AUTOMÁTICO DE PRODUÇÃO
# ================================

set -e  # Parar em caso de erro

echo "🚀 QSDPharmalitics - Setup de Produção"
echo "====================================="

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.production.yml" ]; then
    log_error "docker-compose.production.yml não encontrado!"
    echo "Execute este script no diretório raiz do projeto"
    exit 1
fi

# 1. Criar estrutura de diretórios
log_info "Criando estrutura de diretórios..."
mkdir -p data/{postgres,redis}
mkdir -p logs/nginx
mkdir -p nginx/{conf.d,ssl}
mkdir -p monitoring/grafana/{dashboards,datasources}
mkdir -p static
mkdir -p backups
mkdir -p uploads
mkdir -p reports

# Definir permissões corretas
chmod 755 data/postgres data/redis
chmod 755 backups uploads reports logs

log_info "Diretórios criados com sucesso"

# 2. Verificar se .env.production existe
if [ ! -f ".env.production" ]; then
    log_error "Arquivo .env.production não encontrado!"
    log_info "Criando .env.production com valores padrão..."
    
    cat > .env.production << 'EOF'
# ================================
# CONFIGURAÇÃO DE PRODUÇÃO
# ================================

# Informações da Aplicação
APP_NAME=QSDPharmalitics
APP_VERSION=2.0.0
DEBUG=false

# ================================
# BANCO DE DADOS POSTGRESQL
# ================================
POSTGRES_SERVER=postgres
POSTGRES_USER=admin
POSTGRES_PASSWORD=pe!aa*gh@FURLk.eF77b6hp-u*
POSTGRES_DB=pharmalitics_prod
POSTGRES_PORT=5432

# URL construída automaticamente
DATABASE_URL=postgresql://pharmalitics_user:pe!aa*gh@FURLk.eF77b6hp-u*@postgres:5432/pharmalitics_prod

# ================================
# CACHE REDIS
# ================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=rQAa-hu@P3Ci@cZy6Dx9EFgEKZ
REDIS_DB=0
REDIS_URL=redis://:rQAa-hu@P3Ci@cZy6Dx9EFgEKZ@redis:6379/0

# ================================
# SEGURANÇA
# ================================
SECRET_KEY=8dT6KtvHfCsiAP.BQsNZiRHjEvnA9EruYRGP
API_V1_STR=/api/v1
BACKEND_CORS_ORIGINS=["*"]

# ================================
# PERFORMANCE E CACHE
# ================================
CACHE_TTL_MINUTES=60
ENABLE_CACHE=true
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600

# ================================
# LOGS E MONITORING
# ================================
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=/app/logs/pharmalitics.log

# ================================
# RELATÓRIOS E ARQUIVOS
# ================================
REPORTS_DIR=/app/reports
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=50MB

# ================================
# TIMEZONE E LOCALIZAÇÃO
# ================================
TIMEZONE=America/Sao_Paulo
LOCALE=pt_BR.UTF-8

# ================================
# BACKUP CONFIGURAÇÕES
# ================================
BACKUP_DIR=/app/backups
BACKUP_RETENTION_DAYS=30
AUTO_BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *

# ================================
# PGADMIN
# ================================
PGADMIN_DEFAULT_EMAIL=erickquesada2005@gmail.com
PGADMIN_DEFAULT_PASSWORD=VqNCDQH73.qgnk8ynLUHmzQHKT

# ================================
# WORKERS E PROCESSOS
# ================================
WORKERS_COUNT=4
WORKER_MAX_REQUESTS=1000
WORKER_MAX_REQUESTS_JITTER=50
WORKER_TIMEOUT=120

# ================================
# RATE LIMITING
# ================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_REQUESTS_PER_HOUR=1000
EOF

    log_info "Arquivo .env.production criado"
fi

# 3. Copiar .env.production para .env
log_info "Configurando arquivo .env..."
cp .env.production .env
log_info "Arquivo .env configurado"

# 4. Criar configuração do nginx
log_info "Criando configuração do nginx..."
cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json
        application/xml
        image/svg+xml;

    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=reports:10m rate=2r/s;
    
    upstream pharmalitics_api {
        least_conn;
        server api:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    server {
        listen 80;
        listen [::]:80;
        server_name localhost;
        
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://pharmalitics_api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 16 4k;
        }

        location /api/v1/reports/ {
            limit_req zone=reports burst=5 nodelay;
            
            proxy_pass http://pharmalitics_api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 300s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }

        location /docs {
            proxy_pass http://pharmalitics_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /redoc {
            proxy_pass http://pharmalitics_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }

        error_page 404 /404.html;
        error_page 500 502 503 504 /50x.html;
        
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
EOF

log_info "Configuração do nginx criada"

# 5. Atualizar requirements.txt se necessário
if [ ! -f "requirements.txt" ]; then
    log_warn "requirements.txt não encontrado. Criando..."
    cat > requirements.txt << 'EOF'
# FastAPI Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# Data Validation
pydantic==2.5.0
pydantic-settings==2.0.3

# Data Analysis
pandas==2.1.3
numpy==1.25.2

# Visualization
matplotlib==3.8.2
plotly==5.17.0

# Export
openpyxl==3.1.2
reportlab==4.0.7

# Utils
python-dateutil==2.8.2
python-dotenv==1.0.0
redis==5.0.1
EOF
    log_info "requirements.txt criado"
fi

# 6. Mostrar resumo
echo ""
echo "🎉 Setup de produção concluído!"
echo "================================"
log_info "Diretórios criados:"
echo "   📁 data/{postgres,redis} - Dados persistentes"
echo "   📁 logs/ - Logs da aplicação"
echo "   📁 backups/ - Backups do banco"
echo "   📁 reports/ - Relatórios gerados"
echo "   📁 uploads/ - Arquivos enviados"

log_info "Arquivos configurados:"
echo "   ⚙️  .env - Variáveis de ambiente"
echo "   🌐 nginx/nginx.conf - Configuração do proxy"

echo ""
log_warn "IMPORTANTE: Edite o arquivo .env antes de continuar!"
echo "Mude as senhas padrão para senhas seguras:"
echo "   - POSTGRES_PASSWORD"
echo "   - REDIS_PASSWORD" 
echo "   - SECRET_KEY"
echo "   - PGADMIN_DEFAULT_PASSWORD"

echo ""
echo "📋 Próximos passos:"
echo "1. nano .env  # Editar senhas"
echo "2. docker-compose -f docker-compose.production.yml up -d"
echo "3. curl http://localhost/api/v1/health  # Testar"

echo ""
log_info "Setup finalizado com sucesso! 🚀"
