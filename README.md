# 🏥 QSDPharmalitics API v2.0

> API Python moderna para analytics farmacêutica com FastAPI

## 📋 Sobre o Projeto

QSDPharmalitics é uma API privada desenvolvida para análise de dados farmacêuticos, oferecendo insights sobre vendas, market share, performance de produtos e tendências de mercado.

### ✨ Principais Funcionalidades

- 📊 **Analytics Avançada**: Performance de vendas, market share, tendências
- 📈 **Relatórios Completos**: PDF, Excel, CSV com dados detalhados  
- 🔍 **Dashboard Insights**: KPIs e métricas em tempo real
- 💊 **Gestão de Produtos**: Catálogo completo com categorização
- 🏪 **Análise de Clientes**: Segmentação e valor por farmácia
- 🚀 **API RESTful**: Documentação automática com Swagger

## 🛠️ Tecnologias Utilizadas

- **FastAPI**: Framework web moderno e performático
- **SQLAlchemy**: ORM robusto para banco de dados
- **Pandas**: Análise e manipulação de dados
- **Plotly**: Visualizações interativas
- **PostgreSQL/SQLite**: Bancos de dados suportados
- **Pydantic**: Validação de dados
- **Alembic**: Migrations de banco

## 🚀 Instalação e Configuração

### 1. Pré-requisitos

```bash
# Python 3.11+
python --version

# Git
git --version
```

### 2. Clonagem e Setup

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/QSDPharmalitics.git
cd QSDPharmalitics

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configuração do Banco de Dados

```bash
# Copiar arquivo de ambiente
cp .env.example .env

# Editar configurações no .env
nano .env

# Executar migrations
alembic upgrade head
```

### 4. Executar Aplicação

```bash
# Desenvolvimento
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# A API estará disponível em:
# http://localhost:8000 - API
# http://localhost:8000/docs - Documentação Swagger
# http://localhost:8000/redoc - Documentação ReDoc
```

## 🐳 Executar com Docker

```bash
# Desenvolvimento com PostgreSQL
docker-compose up -d

# Apenas a aplicação (SQLite)
docker build -t pharmalitics .
docker run -p 8000:8000 -v $(pwd):/app pharmalitics
```

## 📚 Documentação da API

### Endpoints Principais

#### 🛒 Vendas (`/api/v1/sales/`)

```http
POST   /api/v1/sales/              # Criar venda
GET    /api/v1/sales/              # Listar vendas
GET    /api/v1/sales/{id}          # Detalhes da venda
PUT    /api/v1/sales/{id}          # Atualizar venda
DELETE /api/v1/sales/{id}          # Excluir venda
```

#### 📊 Analytics (`/api/v1/analytics/`)

```http
GET /api/v1/analytics/sales-performance    # Performance de vendas
GET /api/v1/analytics/market-share         # Market share
GET /api/v1/analytics/trends               # Tendências temporais
GET /api/v1/analytics/top-products         # Produtos top
GET /api/v1/analytics/customer-analysis    # Análise de clientes
GET /api/v1/analytics/revenue-analysis     # Análise de receita
GET /api/v1/analytics/dashboard-summary    # Resumo dashboard
```

#### 📄 Relatórios (`/api/v1/reports/`)

```http
GET /api/v1/reports/sales-summary          # Resumo de vendas
GET /api/v1/reports/monthly                # Relatório mensal
GET /api/v1/reports/comparative            # Comparativo entre períodos
GET /api/v1/reports/export/csv             # Exportar CSV
GET /api/v1/reports/export/excel           # Exportar Excel
GET /api/v1/reports/export/pdf             # Exportar PDF
```

### 📝 Exemplos de Uso

#### Criar uma Venda

```json
POST /api/v1/sales/
{
  "product_name": "Dipirona 500mg",
  "product_category": "Analgésicos",
  "product_code": "DIP500",
  "quantity": 100,
  "unit_price": 2.50,
  "discount": 0.25,
  "pharmacy_name": "Farmácia Central",
  "pharmacy_location": "São Paulo - SP",
  "customer_type": "retail",
  "payment_method": "cartao",
  "sales_rep": "João Silva",
  "notes": "Venda promocional"
}
```

#### Obter Performance de Vendas

```http
GET /api/v1/analytics/sales-performance?start_date=2024-01-01&end_date=2024-01-31&period=day
```

#### Exportar Relatório Excel

```http
GET /api/v1/reports/export/excel?start_date=2024-01-01&end_date=2024-01-31
```

## 🔧 Configuração Avançada

### Banco PostgreSQL

```bash
# No .env
DATABASE_URL=postgresql://user:pass@localhost:5432/pharmalitics

# Ou configurar variáveis separadas:
POSTGRES_SERVER=localhost
POSTGRES_USER=pharmalitics_user
POSTGRES_PASSWORD=sua_senha
POSTGRES_DB=pharmalitics
POSTGRES_PORT=5432
```

### Variáveis de Ambiente

```bash
# .env
APP_NAME=QSDPharmalitics
APP_VERSION=2.0.0
DEBUG=true
SECRET_KEY=sua-chave-super-secreta
DATABASE_URL=sqlite:///./pharmalitics.db
TIMEZONE=America/Sao_Paulo
REPORTS_DIR=./reports
```

## 📊 Estrutura dos Dados

### Modelo de Vendas

```python
{
  "id": 1,
  "product_name": "Dipirona 500mg",
  "product_category": "Analgésicos",
  "product_code": "DIP500",
  "quantity": 100,
  "unit_price": 2.50,
  "total_price": 250.00,
  "discount": 0.00,
  "pharmacy_name": "Farmácia Central",
  "pharmacy_location": "São Paulo - SP",
  "customer_type": "retail",
  "sale_date": "2024-01-15T10:30:00",
  "payment_method": "cartao",
  "sales_rep": "João Silva",
  "campaign_id": "PROMO2024",
  "notes": "Venda promocional",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Testes com cobertura
pytest --cov=app

# Testes específicos
pytest tests/test_sales.py
pytest tests/test_analytics.py
```

## 📈 Analytics Disponíveis

### 🎯 Métricas Principais

- **Receita Total**: Soma de todas as vendas
- **Ticket Médio**: Valor médio por transação
- **Volume de Vendas**: Quantidade total vendida
- **Market Share**: Participação por categoria/produto
- **Taxa de Crescimento**: Comparativo entre períodos

### 📊 Análises Temporais

- **Performance Diária**: Vendas por dia
- **Tendências Mensais**: Evolução ao longo dos meses
- **Sazonalidade**: Padrões por dia da semana/mês
- **Comparativos**: Períodos anterior vs atual

### 🏆 Rankings

- **Top Produtos**: Por receita, quantidade ou frequência
- **Top Clientes**: Farmácias que mais compram
- **Top Categorias**: Categorias mais vendidas
- **Performance por Representante**: Vendas por vendedor

## 🚀 Deployment

### Produção com Docker

```bash
# Build da imagem
docker build -t pharmalitics:production .

# Executar com PostgreSQL
docker-compose -f docker-compose.prod.yml up -d
```

### Configurações de Produção

```bash
# .env.production
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/pharmalitics
SECRET_KEY=sua-chave-super-secreta-de-producao
BACKEND_CORS_ORIGINS=["https://seu-dominio.com"]
```

## 🔐 Segurança

- ✅ Validação de dados com Pydantic
- ✅ Configuração CORS customizável
- ✅ Soft delete para preservar histórico
- ✅ Logs estruturados para auditoria
- 🔜 Autenticação JWT (próxima versão)
- 🔜 Rate limiting (próxima versão)

## 🤝 Comparação Node.js vs Python

### ✅ Vantagens da Migração para Python

| Aspecto | Node.js | Python |
|---------|---------|---------|
| **Analytics** | Limitado | Pandas, NumPy, SciPy |
| **Visualizações** | Chart.js | Matplotlib, Plotly, Seaborn |
| **Data Science** | Básico | Scikit-learn, TensorFlow |
| **Relatórios** | Complexo | ReportLab, openpyxl |
| **Sintaxe** | Callback hell | Mais limpa |
| **Comunidade Data** | Menor | Gigantesca |

### 📊 Performance Esperada

- **I/O Operations**: Similar ao Node.js
- **CPU Intensive**: 3x mais rápido (NumPy/Pandas)
- **Memory Usage**: Mais eficiente para grandes datasets
- **Development Speed**: 40% mais rápido para analytics

## 🔄 Migração do Node.js

### Script de Migração de Dados

```python
# migrate_from_nodejs.py
import json
import pandas as pd
from sqlalchemy import create_engine

def migrate_nodejs_data(json_file_path):
    # Ler dados do Node.js (JSON/CSV)
    with open(json_file_path) as f:
        old_data = json.load(f)
    
    # Converter para formato Python/SQLAlchemy
    # ... lógica de conversão ...
    
    # Inserir no novo banco
    engine = create_engine("sqlite:///./pharmalitics.db")
    df.to_sql("sales", engine, if_exists="append", index=False)
```

## 📞 Suporte e Contribuição

### 🐛 Reportar Issues

1. Verifique se já existe uma issue similar
2. Use o template de bug report
3. Inclua logs e dados de reprodução

### 💡 Novas Features

1. Abra uma discussion primeiro
2. Descreva o caso de uso
3. Aguarde aprovação antes do PR

### 📧 Contato

- **Email**: seu-email@dominio.com
- **Issues**: GitHub Issues
- **Docs**: [Documentação Completa](http://localhost:8000/docs)

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🎉 Conclusão

A **QSDPharmalitics v2.0** representa uma evolução significativa da versão Node.js:

### ✨ Benefícios Imediatos
- **Analytics Nativa**: Pandas e NumPy para análises complexas
- **Relatórios Profissionais**: PDF, Excel com formatação avançada
- **Performance Superior**: Para processamento de dados
- **Código Mais Limpo**: Python é mais legível para analytics

### 🚀 Benefícios Futuros
- **Machine Learning**: Modelos preditivos com scikit-learn
- **Big Data**: Integração com Dask, PySpark
- **Visualizações Avançadas**: Dashboards interativos
- **Automação**: Scripts de análise automatizada

### 📊 ROI da Migração
- **Desenvolvimento**: 40% mais rápido para features analytics
- **Manutenção**: Código mais simples de manter
- **Escalabilidade**: Melhor performance com grandes volumes
- **Insights**: Análises mais profundas e precisas

**Recomendação**: ✅ **Migre para Python!** Para seu caso de uso focado em analytics farmacêutica, os benefícios superam amplamente o esforço de migração.

---

🏥 **QSDPharmalitics** - *Transformando dados farmacêuticos em insights valiosos*



# 🚀 QSDPharmalitics - Configuração de Produção Completa

## 📊 CONTAINERS EM PRODUÇÃO

### 🎯 **Configuração Básica (4 containers):**
```bash
docker-compose -f docker-compose.production.yml up -d
```

**Containers que sobem automaticamente:**
1. 🗄️ **postgres** - Banco PostgreSQL (porta 5432)
2. ⚡ **redis** - Cache (porta 6379)  
3. 🚀 **api** - API FastAPI (porta 8000)
4. 🌐 **nginx** - Proxy reverso (portas 80/443)

**Total: 4 containers rodando**

### 🛠️ **Configuração Completa com Admin (5 containers):**
```bash
docker-compose -f docker-compose.production.yml --profile admin up -d
```

**Containers adicionais:**
5. 🔧 **pgadmin** - Interface PostgreSQL (porta 8080)

**Total: 5 containers rodando**

### 📊 **Configuração Full com Monitoring (8 containers):**
```bash
docker-compose -f docker-compose.production.yml --profile admin --profile monitoring --profile backup up -d
```

**Containers adicionais:**
6. 💾 **backup** - Serviço de backup automático
7. 📈 **prometheus** - Métricas (porta 9090)
8. 📊 **grafana** - Dashboards (porta 3000)

**Total: 8 containers rodando**

## 🔧 CONFIGURAÇÃO PASSO A PASSO

### 1. **Preparar Ambiente:**
```bash
# 1. Criar estrutura de diretórios
mkdir -p data/{postgres,redis} logs/nginx monitoring/grafana/{dashboards,datasources} nginx/{conf.d,ssl} static backups uploads

# 2. Configurar arquivos de ambiente
cp .env.production .env

# 3. Editar configurações críticas
nano .env
```

### 2. **Configurações Obrigatórias no .env:**
```bash
# MUDE ESTAS SENHAS!
POSTGRES_PASSWORD=SuaSenhaPostgreSQL123!
REDIS_PASSWORD=SuaSenhaRedis123!
SECRET_KEY=sua-chave-secreta-256-bits-unica
PGADMIN_DEFAULT_PASSWORD=SenhaPgAdmin123!

# CONFIGURE SEU DOMÍNIO
BACKEND_CORS_ORIGINS=["https://seu-dominio.com"]
```

### 3. **Iniciar Produção (Escolha uma opção):**

#### **🎯 Opção 1: Básica (Recomendada para início)**
```bash
# 4 containers: postgres + redis + api + nginx
docker-compose -f docker-compose.production.yml up -d

# Verificar status
docker-compose -f docker-compose.production.yml ps
```

#### **🛠️ Opção 2: Com Administração**
```bash
# 5 containers: básica + pgadmin
docker-compose -f docker-compose.production.yml --profile admin up -d
```

#### **📊 Opção 3: Full Stack (Produção Avançada)**
```bash
# 8 containers: tudo incluso
docker-compose -f docker-compose.production.yml --profile admin --profile monitoring --profile backup up -d
```

## 🌐 PORTAS E ACESSOS

### **URLs de Acesso:**
- 🚀 **API Principal**: http://localhost/api/v1/
- 📚 **Documentação**: http://localhost/docs
- 🔧 **PgAdmin**: http://localhost:8080 (se --profile admin)
- 📊 **Grafana**: http://localhost:3000 (se --profile monitoring)
- 📈 **Prometheus**: http://localhost:9090 (se --profile monitoring)
- ⚡ **Health Check**: http://localhost/health

### **Portas Internas:**
```
80    -> nginx (HTTP)
443   -> nginx (HTTPS)
5432  -> postgres (interno)
6379  -> redis (interno)
8000  -> api (interno)
8080  -> pgadmin (externo)
3000  -> grafana (externo)
9090  -> prometheus (externo)
```

## 💾 GESTÃO DE DADOS

### **Volumes Persistentes:**
```bash
./data/postgres/     # Dados PostgreSQL
./data/redis/        # Dados Redis
./backups/          # Backups automáticos
./logs/             # Logs da aplicação
./reports/          # Relatórios gerados
./uploads/          # Uploads de arquivos
```

### **Backup Automático:**
```bash
# Backup manual
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U pharmalitics_user pharmalitics_prod > backup.sql

# Ou usar script Python
python scripts/backup_restore.py backup
```

## 🚀 COMANDOS DE PRODUÇÃO

### **Inicialização:**
```bash
# 1. Iniciar stack básica
docker-compose -f docker-compose.production.yml up -d

# 2. Verificar saúde
curl http://localhost/api/v1/health

# 3. Ver logs em tempo real
docker-compose -f docker-compose.production.yml logs -f api

# 4. Aplicar migrations
docker-compose -f docker-compose.production.yml exec api alembic upgrade head
```

### **Monitoramento:**
```bash
# Ver status de todos containers
docker-compose -f docker-compose.production.yml ps

# Recursos utilizados
docker stats

# Logs específicos
docker-compose -f docker-compose.production.yml logs postgres
docker-compose -f docker-compose.production.yml logs api
docker-compose -f docker-compose.production.yml logs nginx
```

### **Manutenção:**
```bash
# Parar tudo
docker-compose -f docker-compose.production.yml down

# Parar e remover volumes (CUIDADO!)
docker-compose -f docker-compose.production.yml down -v
