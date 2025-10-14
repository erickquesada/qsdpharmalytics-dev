# 🚀 Correção Rápida - Erro BACKEND_CORS_ORIGINS

## 📋 Problemas Identificados

### 1. Backend: BACKEND_CORS_ORIGINS
O erro `SettingsError: error parsing value for field "BACKEND_CORS_ORIGINS"` ocorre quando:
1. A variável `BACKEND_CORS_ORIGINS` está vazia no arquivo `.env`
2. A variável está mal formatada (não é um JSON válido)
3. A variável tem espaços em branco ou caracteres inválidos

### 2. Frontend: Node Version
O erro `The engine "node" is incompatible with this module` ocorre porque:
1. O Dockerfile usava Node 18, mas react-router-dom 7.9.4 requer Node 20+
2. CORRIGIDO: Atualizado para Node 20-alpine

## ✅ Solução

### Passo 1: Atualizar o repositório local

```bash
cd /opt/qsdpharma
git pull origin main
```

### Passo 2: Verificar/Criar o arquivo .env

Se você ainda não tem um arquivo `.env`, crie um:

```bash
cd /opt/qsdpharma
cp .env.production.example .env
```

### Passo 3: Editar o arquivo .env

Abra o arquivo `.env` e verifique se as seguintes variáveis estão configuradas:

```bash
nano .env
```

**IMPORTANTE**: Configure estas variáveis obrigatórias:

```bash
# Senha do PostgreSQL (use uma senha forte!)
POSTGRES_PASSWORD=SuaSenhaForteAqui123!@#

# Chave secreta (gere com: openssl rand -hex 32)
SECRET_KEY=cole_aqui_a_chave_gerada

# CORS - FORMATO JSON CORRETO (copie exatamente assim!)
BACKEND_CORS_ORIGINS=["https://qsdpharma.qsdconnect.cloud"]

# Domínio
DOMAIN=qsdpharma.qsdconnect.cloud
```

**ATENÇÃO**: O `BACKEND_CORS_ORIGINS` DEVE ser um array JSON válido:
- ✅ CORRETO: `["https://qsdpharma.qsdconnect.cloud"]`
- ✅ CORRETO: `["https://qsdpharma.qsdconnect.cloud","https://outro.com"]`
- ❌ ERRADO: `https://qsdpharma.qsdconnect.cloud`
- ❌ ERRADO: `BACKEND_CORS_ORIGINS=`
- ❌ ERRADO: `[ "https://qsdpharma.qsdconnect.cloud" ]` (espaços extras)

### Passo 4: Parar containers existentes

```bash
cd /opt/qsdpharma
docker-compose -f docker-compose.production.yml down
```

### Passo 5: Reconstruir e iniciar

```bash
cd /opt/qsdpharma
docker-compose -f docker-compose.production.yml up --build -d
```

### Passo 6: Verificar os logs

```bash
# Ver logs do backend
docker logs qsdpharma_backend

# Ver logs do frontend
docker logs qsdpharma_frontend

# Ver status dos containers
docker ps
```

## 🔍 Verificação

O backend deve iniciar sem erros. Você deve ver:

```
✅ PostgreSQL is ready!
✅ Migrations completed successfully!
✅ Admin user created successfully!
🚀 Starting application...
```

## 🌐 Teste de API

Teste se o backend está respondendo:

```bash
curl http://localhost:8001/api/v1/health
```

Deve retornar: `{"status":"healthy"}`

## 🆘 Se ainda houver problemas

1. **Verifique o formato do .env**:
```bash
cat /opt/qsdpharma/.env | grep BACKEND_CORS_ORIGINS
```

2. **Logs detalhados**:
```bash
docker logs qsdpharma_backend --tail 100
```

3. **Reinicie completamente**:
```bash
docker-compose -f docker-compose.production.yml down -v
docker-compose -f docker-compose.production.yml up --build -d
```

## 📝 Arquivo .env Mínimo Funcional

Se quiser começar do zero, use este `.env` mínimo:

```bash
# Database
POSTGRES_DB=pharmalitics
POSTGRES_USER=pharmalitics_user
POSTGRES_PASSWORD=MudeEstaSenha123!@#

# App
SECRET_KEY=cole_aqui_uma_chave_de_32_caracteres_ou_mais
ENVIRONMENT=production
DEBUG=False

# Domain
DOMAIN=qsdpharma.qsdconnect.cloud

# CORS - COPIE EXATAMENTE ASSIM!
BACKEND_CORS_ORIGINS=["https://qsdpharma.qsdconnect.cloud"]

# API
API_V1_STR=/api/v1
```

## ✨ Melhorias Aplicadas

1. ✅ Validador robusto para `BACKEND_CORS_ORIGINS` que aceita JSON ou string vazia
2. ✅ Imports corrigidos no `docker-entrypoint.sh`
3. ✅ Método `get_database_url()` usado corretamente no Alembic
4. ✅ Logs melhorados com emojis para fácil identificação
5. ✅ Tratamento de erros aprimorado
6. ✅ Docker Compose atualizado para passar variáveis corretamente
