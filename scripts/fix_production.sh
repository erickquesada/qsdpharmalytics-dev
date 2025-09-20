#!/bin/bash

echo "🔧 Corrigindo problema do Gunicorn..."

# 1. Parar containers
echo "⏹️  Parando containers..."
docker compose -f docker-compose.production.yml down

# 2. Remover imagem da API para forçar rebuild
echo "🗑️  Removendo imagem antiga..."
docker image rm qsdpharmalitics-api 2>/dev/null || echo "   Imagem não encontrada (ok)"

# 3. Atualizar requirements.txt
echo "📦 Atualizando requirements.txt..."
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

# Plotting
matplotlib==3.8.2
plotly==5.17.0

# Export
openpyxl==3.1.2
reportlab==4.0.7

# Utils
python-dateutil==2.8.2
python-dotenv==1.0.0
redis==5.0.1
psutil==5.9.6
httpx==0.25.2
EOF

echo "✅ requirements.txt atualizado"

# 4. Rebuild e iniciar
echo "🔨 Rebuilding containers..."
docker compose -f docker-compose.production.yml up -d --build

echo "✅ Correção aplicada!"
echo ""
echo "🔍 Verificando status..."
sleep 10
docker compose -f docker-compose.production.yml ps
